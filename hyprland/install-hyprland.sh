#!/bin/bash -eu

# Inspired By SolDoesTech - https://www.youtube.com/@SolDoesTech

# The follwoing will attempt to install all needed packages to run Hyprland
# This is a quick and dirty script there are some error checking

# Define the software that would be installed
prep_stage=(
  qt5ct
  qt6ct
  gtk3
  polkit-gnome
  pipewire    # Media sharing server
  wireplumber # session manager for pipewire
  jq          # CLI json parser
)

#the main packages
install_stage=(
  mako     # Notification daemon for Wayland
  waybar   # Statusbar
  hyprlock # swaylock-effects doesn't work due to the "input inhibit handling"
  wofi     # appliaction launcher for wayland
  wlogout  # systemctl hibernate does currently not work due to "swap memory to small"
  xdg-desktop-portal-hyprland
  swappy      # Wayland snapshot editing tool
  grim        # Screenshot tool for Sway
  slurp       # Region selector in Sway
  pamixer     # CLI for pulseaudio
  pavucontrol # Volume control GUI for pulseaudio
  brightnessctl
  bluez
  blueman
  network-manager-applet
)

for str in ${myArray[@]}; do
  echo $str
done

# set some colors
CNT="[\e[1;36mNOTE\e[0m]"
CPK="[\e[1;36mPKG\e[0m]"
COK="[\e[1;32mOK\e[0m]"
CER="[\e[1;31mERROR\e[0m]"
CWR="[\e[1;35mWARNING\e[0m]"
INSTLOG="installation.log"

######
# functions go here

# function that would show a progress bar to the user
show_progress() {
  while ps | grep $1 &>/dev/null; do
    echo -n "."
    sleep 2
  done
  echo -en "Done!\n"
  sleep 2
}

install_cliphist() {
  CH="cliphist"
  mkdir $CH
  cd $CH
  echo -e "$CNT - Downloading binaries for $CH (v0.5.0)"
  wget -q https://github.com/sentriz/cliphist/releases/download/v0.5.0/v0.5.0-linux-amd64
  mv v0.5.0-linux-amd64 $CH
  echo -e "$CNT - Setting permissions for $CH"
  chmod +x $CH
  echo -e "$CNT - Moving $CH binaries to /usr/bin"
  sudo cp $CH /usr/bin
  cd ..
  rm -rf $CH
  echo -e "$COK - $CH was installed"
}

# function that will test for a package and if not found it will attempt to install it
install_software() {
  # First lets see if the package is there
  if sudo dnf list installed $1 -q &>>/dev/null; then
    echo -e "$COK - $1 is already installed."
  else
    # no package found so installing
    echo -en "$CNT - Now installing $1 ."
    sudo dnf install $1 --assumeyes &>>$INSTLOG
    show_progress $!
    # test to make sure package installed
    if sudo dnf list installed $1 -q &>>/dev/null; then
      echo -e "\e[1A\e[K$COK - $1 was installed."
    else
      # if this is hit then a package is missing, exit to review log
      echo -e "\e[1A\e[K$CER - $1 install had failed, please check the install.log"
      exit 1
    fi
  fi
}

# function that backs up potential existing data and then overwrites it with a symlink to the new folders
backup_and_link() {
  SCRIPT_DIR="$(cd "$(dirname $0)" && pwd)"
  CONFIG_DIR="$HOME/.config"
  BACKUP_DIR="$HOME/backups"
  SOURCE="$1"
  TARGET="$2"

  mkdir -p $BACKUP_DIR

  # Backup target folder if it exists
  if [[ -d "$TARGET" ]]; then
    TIMESTAMP=$(date +%Y%m%d%H%M)
    echo -e "$CNT - Creating backup $BACKUP_DIR/$TARGET.bak.$TIMESTAMP"
    cp -rL "$CONFIG_DIR/$TARGET" "$BACKUP_DIR/$TARGET.bak.$TIMESTAMP"

    rm -rf "$CONFIG_DIR/$TARGET"
  fi

  ln -sf "$SCRIPT_DIR/$SOURCE" "$CONFIG_DIR/$TARGET"
  echo -e "$COK - Symlink created from $SCRIPT_DIR/$SOURCE to $CONFIG_DIR/$TARGET"
}

# set some expectations for the user
echo -e "$CNT - You are about to execute a script that would attempt to setup Hyprland.
Please note that Hyprland is still in Beta."
sleep 1

# attempt to discover if this is a VM or not
echo -e "$CNT - Checking for Physical or VM..."
ISVM=$(hostnamectl | grep Chassis)
echo -e "Using $ISVM"
if [[ $ISVM == *"vm"* ]]; then
  echo -e "$CWR - Please note that VMs are not fully supported and if you try to run this on
    a Virtual Machine there is a high chance this will fail."
  sleep 1
fi

# let the user know that we will use sudo
echo -e "$CNT - This script will run some commands that require sudo. You will be prompted to enter your password.
If you are worried about entering your password then you may want to review the content of the script."
sleep 1

# give the user an option to exit out
read -rep $'[\e[1;33mACTION\e[0m] - Would you like to continue with the install (y,n) ' CONTINST
if [[ $CONTINST != "Y" && $CONTINST != "y" ]]; then
  echo -e "$CNT - This script will now exit, no changes were made to your system."
  exit
fi
echo -e "$CNT - Setup starting..."

### Install all of the above pacakges ####
echo -e "$CNT - PREPARATION Packages..."
for SOFTWR in ${prep_stage[@]}; do
  echo -e "$CPK - $SOFTWR"
done
echo -e "$CNT - MAIN Packages..."
for SOFTWR in ${install_stage[@]}; do
  echo -e "$CPK - $SOFTWR"
done

read -rep $'[\e[1;33mACTION\e[0m] - Would you like to install the packages? (y,n) ' INST
if [[ $INST == "Y" || $INST == "y" ]]; then

  # Prep Stage - Bunch of needed items
  echo -e "$CNT - Prep Stage - Installing needed components, this may take a while..."
  for SOFTWR in ${prep_stage[@]}; do
    install_software $SOFTWR
  done

  # Install the correct hyprland version
  echo -e "$CNT - Installing Hyprland, this may take a while..."
  install_software hyprland

  # Stage 1 - main components
  echo -e "$CNT - Installing main components, this may take a while..."
  for SOFTWR in ${install_stage[@]}; do
    install_software $SOFTWR
  done

  # Start the bluetooth service
  echo -e "$CNT - Starting the Bluetooth Service..."
  sudo systemctl enable --now bluetooth.service &>>$INSTLOG
  sleep 2
fi

read -rep $'[\e[1;33mACTION\e[0m] - Would you like to install a clipboard manager (note that linux-amd64 is assumed)? (y,n) ' CONTINST
if [[ $CONTINST == "Y" || $CONTINST == "y" ]]; then
  install_software wl-clipboard
  install_cliphist
fi

### Copy Config Files ###
read -rep $'[\e[1;33mACTION\e[0m] - Would you like to copy config files? (y,n) ' CFG
if [[ $CFG == "Y" || $CFG == "y" ]]; then

  # Make all shell-scripts in this folder executable
  SCRIPT_NAME="$(basename $0)"
  SCRIPT_DIR="$(cd "$(dirname $0)" && pwd)"
  echo -e "$CNT - Making all shell-scripts in $SCRIPT_DIR executable"
  find $SCRIPT_DIR -type f -name "*.sh" | while read -r FILE; do
    if [[ "$(basename "$FILE")" != $SCRIPT_NAME ]]; then
      chmod +x $FILE
      echo -e "$COK - $FILE made executable"
    fi
  done

  echo -e "$CNT - Copying config files..."
  backup_and_link "hypr" "hypr"
  backup_and_link "backgrounds" "backgrounds"
  backup_and_link "swappy" "swappy"
  backup_and_link "waybar" "waybar"
  backup_and_link "wlogout" "wlogout"
  backup_and_link "wofi" "wofi"
  backup_and_link "hyprland-media-scripts" "hyprland-media-scripts"
fi

### Script is done ###
echo -e "$CNT - Script has completed!"
