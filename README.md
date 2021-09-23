# ConsoleSnake

![](https://img.shields.io/badge/license-MIT-blueviolet.svg)
![](https://tokei.rs/b1/github/XDead27/ConsoleSnake?category=code)
![](https://img.shields.io/github/v/release/XDead27/ConsoleSnake?include_prereleases)

A multiplayer snake game with a TUI, written in python.

![Demo](https://user-images.githubusercontent.com/32306451/134492672-319f0067-ee8a-487d-8487-d8d8d329d349.gif)

The terminal in the demo above is a customized termite.

![Demo](https://user-images.githubusercontent.com/32306451/134492701-5b0d8267-3faa-448b-9596-15c61418e60a.gif)

## Installation

The project is not yet in any repositories. You can find the packages on the [releases page](https://github.com/XDead27/ConsoleSnake/releases).

### Arch

1. Download the binary from the [releases page](https://github.com/XDead27/ConsoleSnake/releases).

2. Install the package using `packman`.
```
# pacman -U /path/to/binary
```

### Debian

1. Download the binary from the [releases page](https://github.com/XDead27/ConsoleSnake/releases).

2. Install the package using `dpkg`.
```
# dpkg -i /path/to/binary
```

### Manual Installation

1. Clone the project (https://github.com/XDead27/ConsoleSnake.git)

2. `cd` into the ConsoleSnake directory

3. Install dependencies
```
$ make requirements
```
or
```
$ pip3 install numpy art argparse
```

4. Run the `make` command
```
# make install
```

## Usage

The app is divided into the client (`consolesnake`) and the server (`consolesnake-server`).
To run the game, you need to connect to a server, either online or on your local machine.

#### TL;DR 
Run these 2 commands in different terminal instances:
```
$ consolesnake-client
$ consolesnake
```

### Server

The binary is named `consolesnake-server`.

Running `consolesnake-server` with no arguments will start a server on address `127.0.0.1` (loopback) and port `1403`.
If you want to specify an address and a port you can do it as follows:
```
$ consolesnake-server <host> <port>
```

### Client

The binary is named `consolesnake`.

Once you have a running server to connect to, either online or on your machine, you can start the client.
Running `consolesnake` with no arguments will spawn an instance of the game that connects to a server located at address `127.0.0.1` (loopback) and port `1403`.
If you want to specify an address and a port you can do it as follows:
```
$ consolesnake [-p PORT] [-b HOST]
```
You can get more command information by running `consolesnake --help`.

## End Note

Please keep in mind this project is far from finished, or actually being a useful piece of software. Bugs are (very) common and the app might break or not work on your machine.

That being said, help is wanted if you find this project interesting! :>
