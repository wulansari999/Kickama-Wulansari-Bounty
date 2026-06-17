# Contributing

Thank you for your interest in contributing to Zeroeye / Tent of Trials. This guide covers the usual local setup, build, test, and pull-request workflow for the Python tooling, Rust backend, and TypeScript frontend in this repository.

## Clone the repository

Fork the repository on GitHub, then clone your fork and add the upstream remote:

```sh
git clone https://github.com/<your-username>/zeroeye.git
cd zeroeye
git remote add upstream https://github.com/lobster-trap/zeroeye.git
git fetch upstream
```

Create feature branches from the latest upstream `main`:

```sh
git checkout main
git pull --ff-only upstream main
git checkout -b feature/your-change
```

## Install dependencies

### System packages

On Debian/Ubuntu, install the common tools used by the Python build orchestrator, Rust backend, and TypeScript frontend:

```sh
sudo apt update
sudo apt install -y build-essential curl ca-certificates gnupg pkg-config libssl-dev protobuf-compiler python3
```

Install Rust with rustup if it is not already available:

```sh
curl https://sh.rustup.rs -sSf | sh -s -- -y
. "$HOME/.cargo/env"
```

Install Node.js 22 if Node/npm are not already available:

```sh
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
```

### Project dependencies

The root Python build script uses the Python standard library. Install module-specific dependencies before building:

```sh
# Rust backend
cargo fetch --manifest-path backend/Cargo.toml

# TypeScript frontend
cd frontend
npm ci
cd ..
```

## Build

Use the repository build orchestrator from the root directory:

```sh
python3 build.py
```

Useful variants:

```sh
python3 build.py --module backend
python3 build.py --module frontend
python3 build.py --module backend,frontend
python3 build.py --release
python3 build.py --clean
```

The build writes diagnostic artifacts under `diagnostic/`. The current GitHub workflow checks pull requests for new `diagnostic/*.logd` and `diagnostic/*.json` files, so include the generated diagnostic bundle in your PR unless a maintainer asks otherwise.

You can also build individual modules directly:

```sh
# Rust backend
cd backend
cargo build
cd ..

# TypeScript frontend
cd frontend
npm run build
cd ..
```

## Run tests and checks

Run the checks that apply to the files you changed:

```sh
# Python syntax checks for root tooling and helper scripts
python3 -m compileall build.py tools

# Rust backend tests
cd backend
cargo test
cd ..

# TypeScript frontend type-check and production build
cd frontend
npm run build
cd ..
```

If you touch other modules, run their native checks as well, for example `go test ./...` from `market/` or `make test` from `frailbox/` when those toolchains are available.

## Submit a pull request

1. Keep your branch focused on one issue or change.
2. Format code consistently with the surrounding files.
3. Run the relevant build and test commands.
4. Commit the code and any required diagnostic files:

   ```sh
   git status
   git add <changed-files> diagnostic/<generated-files>
   git commit -m "Describe the change"
   ```

5. Push your branch to your fork:

   ```sh
   git push -u origin feature/your-change
   ```

6. Open a pull request against `lobster-trap/zeroeye:main`. In the PR description, link the related issue, summarize the change, list the checks you ran, and mention any diagnostics included.

Respond promptly to review feedback and keep the branch up to date with `main` when requested.
