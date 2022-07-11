


#
mdt push /home/baset/Activity/clarkson/pChallange2022/wpi_prosthetic /home/mendel



# 2: Install MDT
MDT is a command line tool for your host computer that helps you interact with the Dev Board Mini. For example, MDT can list connected devices, install Debian packages on the board, and open a shell terminal on the board.
You can install MDT on your host computer follows:

python3 -m pip install --user mendel-development-tool

You might see a warning that mdt was installed somewhere that's not in your PATH environment variable. If so, be sure you add the given location to your PATH, as appropriate for your operating system. If you're on Linux, you can add it like this:

echo 'export PATH="$PATH:$HOME/.local/bin"' >> ~/.bash_profile
source ~/.bash_profile


# 3: Plug in the board
Connect your power supply to the board's USB power plug (the left plug, as shown in figure 1) and connect it to an outlet.
Connect your USB data cable to the other USB plug and to your host computer.
When you connect the USB cable to your computer, the board automatically boots up, and the board's LED turns green. It then takes 20-30 seconds for the system to boot up.


