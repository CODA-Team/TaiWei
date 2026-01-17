#!/usr/bin/env python3
import argparse
import os
import signal
import socket
import subprocess
import sys
import shlex
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple


# ==============================================================================
# Safety: signals + process-group kill
# ==============================================================================

def _install_signal_handlers():
    """Install signal handlers so that SIGINT/SIGTERM raise KeyboardInterrupt."""
    def _handler(signum, frame):
        raise KeyboardInterrupt()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _handler)
        except Exception:
            pass


def _run_command_with_log(
    cmd: Sequence[str],
    log_path: Path,
    cwd: Optional[Path] = None,
    env: Optional[dict] = None,
):
    """
    Run a command, redirect stdout/stderr to log_path.
    Start a new process group so we can kill the whole tree via killpg on interrupt.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # 兼容性处理：Windows/非POSIX环境没有 os.setsid
    preexec = getattr(os, "setsid", None)

    with open(log_path, "w") as log_file:
        proc = subprocess.Popen(
            list(cmd),
            stdout=log_file,
            stderr=subprocess.STDOUT,
            cwd=str(cwd) if cwd else None,
            preexec_fn=preexec,
            env=env,
        )

        try:
            ret = proc.wait()
            if ret != 0:
                raise subprocess.CalledProcessError(ret, list(cmd))
        except KeyboardInterrupt:
            try:
                if preexec and hasattr(os, "killpg"):
                    os.killpg(proc.pid, signal.SIGTERM)
                else:
                    proc.terminate()
            except Exception:
                pass
            raise
        except Exception:
            try:
                if preexec and hasattr(os, "killpg"):
                    os.killpg(proc.pid, signal.SIGTERM)
                else:
                    proc.terminate()
            except Exception:
                pass
            raise


# ==============================================================================
# Experiment definitions
# ==============================================================================

@dataclass(frozen=True)
class RunConfig:
    flow: str                 # "ord" or "cds"
    tech: str
    case: str
    remote_user: str
    remote_host: str
    remote_project_dir: str   # only for ord eval (ssh)
    repo_root: Path           # local repo root (where test/ exists)
    ord_eval_mode: str        # "local" or "remote"
    ord_eval_ssh_opts: str
    do_run: bool
    do_eval: bool


def _log_paths(flow: str, tech: str, case: str) -> Tuple[Path, Path]:
    base = Path(f"run_logs/{tech}/{flow}")
    run_log = base / "run" / f"{case}_run.log"
    eval_log = base / "eval" / f"{case}_eval.log"
    return run_log, eval_log


def _script_paths(repo_root: Path, flow: str, tech: str, case: str) -> Tuple[Path, Path]:
    run_script = repo_root / "test" / tech / case / flow / "run.sh"
    eval_script = repo_root / "test" / tech / case / flow / "eval.sh"
    return run_script, eval_script


def _load_env_from_script(env_script: Path) -> None:
    if not env_script.exists():
        return
    cmd = [
        "bash",
        "-lc",
        f'export FLOW_ENV_QUIET=1; source "{env_script}"; env -0',
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    for entry in proc.stdout.split(b"\0"):
        if not entry:
            continue
        key, _, value = entry.partition(b"=")
        os.environ[key.decode(errors="ignore")] = value.decode(errors="ignore")


def run_one(cfg: RunConfig) -> str:
    """
    Execute one (flow, tech, case) task.
    - cds: run.sh + eval.sh locally
    - ord: run.sh locally; eval.sh via ssh (logs local)
    """
    _install_signal_handlers()
    _load_env_from_script(cfg.repo_root / "env.sh")

    pid = os.getpid()
    host = socket.gethostname()

    run_log, eval_log = _log_paths(cfg.flow, cfg.tech, cfg.case)
    # 兼容 Python 3.6: unlink(missing_ok=True) 改为 try-except
    if cfg.do_run:
        try:
            run_log.unlink()
        except FileNotFoundError:
            pass
    if cfg.do_eval:
        try:
            eval_log.unlink()
        except FileNotFoundError:
            pass

    run_script, eval_script = _script_paths(cfg.repo_root, cfg.flow, cfg.tech, cfg.case)

    mode = "run+eval"
    if cfg.do_run and not cfg.do_eval:
        mode = "run-only"
    elif cfg.do_eval and not cfg.do_run:
        mode = "eval-only"
    print(f"[{pid}] Start {cfg.flow.upper()} tech={cfg.tech} case={cfg.case} mode={mode} on host={host}")

    # --- run.sh (local) ---
    if cfg.do_run:
        if not run_script.exists():
            msg = f"[{pid}] ERROR: run.sh not found: {run_script}"
            print(msg)
            return msg

        try:
            _run_command_with_log(
                ["bash", str(run_script)],
                run_log,
                cwd=cfg.repo_root,
                env=os.environ.copy(),
            )
        except subprocess.CalledProcessError:
            msg = f"[{pid}] ERROR: run.sh failed ({cfg.flow}/{cfg.tech}/{cfg.case}). See {run_log}"
            print(msg)
            return msg

    # --- eval.sh ---
    if not cfg.do_eval:
        ok = f"[{pid}] OK: {cfg.flow}/{cfg.tech}/{cfg.case}"
        print(ok)
        return ok
    if cfg.flow == "cds":
        if not eval_script.exists():
            msg = f"[{pid}] ERROR: eval.sh not found: {eval_script}"
            print(msg)
            return msg
        try:
            _run_command_with_log(
                ["bash", str(eval_script)],
                eval_log,
                cwd=cfg.repo_root,
                env=os.environ.copy(),
            )
        except subprocess.CalledProcessError:
            msg = f"[{pid}] ERROR: eval.sh failed ({cfg.flow}/{cfg.tech}/{cfg.case}). See {eval_log}"
            print(msg)
            return msg

    elif cfg.flow == "ord":
        # Local path exists check (remote may differ, but at least validate naming)
        if not eval_script.exists():
            msg = f"[{pid}] ERROR: eval.sh not found locally (for naming sanity): {eval_script}"
            print(msg)
            return msg

        if cfg.ord_eval_mode == "remote":
            remote_eval_script = f"test/{cfg.tech}/{cfg.case}/ord/eval.sh"
            remote_cmd = (
                "set -euo pipefail; "
                f"cd {cfg.remote_project_dir}; "
                'echo "[remote] CWD=$PWD"; '
                f"bash {remote_eval_script}"
            )

            ssh_target = f"{cfg.remote_user}@{cfg.remote_host}"
            ssh_cmd = ["ssh"]
            if cfg.ord_eval_ssh_opts:
                ssh_cmd.extend(shlex.split(cfg.ord_eval_ssh_opts))
            ssh_cmd.extend(["-t", ssh_target, "bash", "-lc", "--", remote_cmd])
            try:
                _run_command_with_log(
                    ssh_cmd,
                    eval_log,
                    cwd=cfg.repo_root,
                    env=os.environ.copy(),
                )
            except subprocess.CalledProcessError:
                msg = f"[{pid}] ERROR: remote eval.sh failed ({cfg.flow}/{cfg.tech}/{cfg.case}). See {eval_log}"
                print(msg)
                return msg
        else:
            try:
                _run_command_with_log(
                    ["bash", str(eval_script)],
                    eval_log,
                    cwd=cfg.repo_root,
                    env=os.environ.copy(),
                )
            except subprocess.CalledProcessError:
                msg = f"[{pid}] ERROR: eval.sh failed ({cfg.flow}/{cfg.tech}/{cfg.case}). See {eval_log}"
                print(msg)
                return msg
    else:
        return f"[{pid}] ERROR: unknown flow={cfg.flow}"

    ok = f"[{pid}] OK: {cfg.flow}/{cfg.tech}/{cfg.case}"
    print(ok)
    return ok


# ==============================================================================
# CLI + orchestration
# ==============================================================================

def _dedup_keep_order(xs: Iterable[str]) -> List[str]:
    seen = set()
    out = []
    for x in xs:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def build_tasks(
    flows: List[str],
    techs: List[str],
    cases: List[str],
    remote_user: str,
    remote_host: str,
    remote_project_dir: str,
    repo_root: Path,
    ord_eval_mode: str,
    ord_eval_ssh_opts: str,
    do_run: bool,
    do_eval: bool,
) -> List[RunConfig]:
    tasks: List[RunConfig] = []
    for flow in flows:
        for tech in techs:
            for case in cases:
                tasks.append(
                    RunConfig(
                        flow=flow,
                        tech=tech,
                        case=case,
                        remote_user=remote_user,
                        remote_host=remote_host,
                        remote_project_dir=remote_project_dir,
                        repo_root=repo_root,
                        ord_eval_mode=ord_eval_mode,
                        ord_eval_ssh_opts=ord_eval_ssh_opts,
                        do_run=do_run,
                        do_eval=do_eval,
                    )
                )
    return tasks


def parse_args(
    default_remote_user: str,
    default_remote_host: str,
    default_remote_project_dir: str,
    default_repo_root: Optional[str],
    default_ord_eval_mode: str,
    default_ord_eval_ssh_opts: str,
) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run ORFS experiments (ORD/CDS) in parallel with per-task logs."
    )
    p.add_argument(
        "--flow",
        choices=["ord", "cds", "all"],
        default="all",
        help="Which flow to run (default: all).",
    )
    p.add_argument(
        "--tech",
        action="append",
        default=[],
        help="Tech name. Repeatable. Default: run all preset techs.",
    )
    p.add_argument(
        "--case",
        action="append",
        default=[],
        help="Case/design name. Repeatable. Default: run all preset cases.",
    )
    p.add_argument(
        "--jobs",
        type=int,
        default=9,
        help="Parallel workers.",
    )
    stage_group = p.add_mutually_exclusive_group()
    stage_group.add_argument(
        "--eval-only",
        action="store_true",
        help="Only run eval.sh for each task.",
    )
    stage_group.add_argument(
        "--run-only",
        action="store_true",
        help="Only run run.sh for each task.",
    )

    # ORD remote eval controls (kept explicit)
    p.add_argument("--remote-user", default=default_remote_user, help="SSH user for ORD eval.")
    p.add_argument("--remote-host", default=default_remote_host, help="SSH host for ORD eval.")
    p.add_argument(
        "--remote-project-dir",
        default=default_remote_project_dir,
        help="Remote repo root for ORD eval.",
    )
    p.add_argument(
        "--ord-eval-mode",
        choices=["local", "remote"],
        default=default_ord_eval_mode,
        help="Where to run ORD eval.sh (default from env: ORD_EVAL_MODE).",
    )
    p.add_argument(
        "--ord-eval-ssh-opts",
        default=default_ord_eval_ssh_opts,
        help="Extra ssh options for remote ORD eval (default from env: ORD_EVAL_SSH_OPTS).",
    )

    p.add_argument(
        "--repo-root",
        default=default_repo_root,
        help="Local repo root path (default: env FLOW_HOME or script parent).",
    )
    return p.parse_args()


def main() -> int:
    _install_signal_handlers()
    script_root = Path(__file__).resolve().parent
    _load_env_from_script(script_root / "env.sh")

    default_repo_root = os.environ.get("FLOW_HOME", str(script_root))
    default_remote_user = os.environ.get("ORD_EVAL_REMOTE_USER", "zhiyuzheng")
    default_remote_host = os.environ.get("ORD_EVAL_REMOTE_HOST", socket.gethostname())
    default_remote_project_dir = os.environ.get(
        "ORD_EVAL_REMOTE_PROJECT_DIR", default_repo_root
    )
    default_ord_eval_mode = os.environ.get("ORD_EVAL_MODE", "local").lower()
    if default_ord_eval_mode not in {"local", "remote"}:
        default_ord_eval_mode = "local"
    default_ord_eval_ssh_opts = os.environ.get("ORD_EVAL_SSH_OPTS", "")

    args = parse_args(
        default_remote_user=default_remote_user,
        default_remote_host=default_remote_host,
        default_remote_project_dir=default_remote_project_dir,
        default_repo_root=default_repo_root,
        default_ord_eval_mode=default_ord_eval_mode,
        default_ord_eval_ssh_opts=default_ord_eval_ssh_opts,
    )

    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parent

    # Default suites (match your originals)
    default_techs = ["asap7_3D", "nangate45_3D", "asap7_nangate45_3D"]
    default_cases = ["gcd", "aes", "jpeg", "ibex"]

    techs = _dedup_keep_order(args.tech) if args.tech else default_techs
    cases = _dedup_keep_order(args.case) if args.case else default_cases

    if args.flow == "all":
        flows = ["ord", "cds"]
    else:
        flows = [args.flow]

    do_run = not args.eval_only
    do_eval = not args.run_only

    tasks = build_tasks(
        flows=flows,
        techs=techs,
        cases=cases,
        remote_user=args.remote_user,
        remote_host=args.remote_host,
        remote_project_dir=args.remote_project_dir,
        repo_root=repo_root,
        ord_eval_mode=args.ord_eval_mode,
        ord_eval_ssh_opts=args.ord_eval_ssh_opts,
        do_run=do_run,
        do_eval=do_eval,
    )

    print(f"[MAIN] repo_root={repo_root}")
    print(f"[MAIN] flows={flows} techs={techs} cases={cases} jobs={args.jobs}")
    print(f"[MAIN] stages: run={do_run} eval={do_eval}")
    print(f"[MAIN] total_tasks={len(tasks)} logs under run_logs/<tech>/<flow>/...")
    print(
        "[MAIN] env CDS_PARTITION_MODE={}"
        " ORD_EVAL_MODE={}".format(
            os.environ.get("CDS_PARTITION_MODE", "docker"),
            os.environ.get("ORD_EVAL_MODE", "local"),
        )
    )

    # Run
    executor: Optional[ProcessPoolExecutor] = None
    try:
        with ProcessPoolExecutor(max_workers=args.jobs) as executor:
            futures = [executor.submit(run_one, t) for t in tasks]
            for fut in as_completed(futures):
                _ = fut.result()
    except KeyboardInterrupt:
        print("[MAIN] KeyboardInterrupt received, shutting down...")
        if executor is not None:
            try:
                executor.shutdown(wait=False, cancel_futures=True)
            except Exception:
                pass
        return 130

    print("[MAIN] All experiments completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
