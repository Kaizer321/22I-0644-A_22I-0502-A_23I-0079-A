import subprocess
import sys

from src import analysis, campaign, experiments, loader


def verify():
    n = len(loader.verify_checksums())
    print(f"{loader.RELEASE}: {n} files, checksums OK")
    return 0


def test():
    return subprocess.run([sys.executable, "-m", "pytest", "tests", "-q"]).returncode


def main(argv):
    cmd, args = (argv[0], argv[1:]) if argv else ("all", [])
    cmds = {"verify": verify, "test": test, "campaign": lambda: campaign.campaign(args),
            "experiments": lambda: experiments.main(args), "analyse": lambda: analysis.main(args)}
    if cmd == "all":
        for c in ("verify", "test", "campaign", "experiments", "analyse"):
            if main([c]):
                return 1
        return 0
    if cmd not in cmds:
        print("usage: python -m src.main verify|test|campaign [case_ids...]|experiments [EXP...] [--smoke]|analyse [--smoke]|all")
        return 2
    return int(bool(cmds[cmd]()))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
