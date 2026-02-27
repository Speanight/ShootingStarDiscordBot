#!/bin/bash
cd /var/ShootingStarDiscordBot || exit

if [ ! $1 ]; then
  exit
fi

for arg in "$@"; do
  case "$arg" in
    -h|--help)
      echo "======| Help message |====="
      echo "This util allows you to update the Shooting Star discord bot thanks to the github."
      echo "It will check the difference between the tags to see if you're on the latest version or not."
      echo "The command needs one (or more) of the following arguments."
      echo "===| Arguments |==="
      echo "-h / --help | Displays this message."
      echo "-i / --info | Displays the installed version"
      echo "-c / --check | Check if an update is available. Returns 0 if none, otherwise return the latest versions tag name."
      echo "-u / --update | Updates the bot (if possible) to the latest version. Beta versions included!"
    ;;
    -i|--info)
      echo $(git tag -n | tail -n 1)
    ;;
    -c|--check)
      git fetch origin
      LOCAL=$(git rev-parse @)
      REMOTE=$(git rev-parse origin/main)
      VERSION=$(git describe --tags $(git rev-list --tags --max-count=1))

      if [ "$LOCAL" = "$REMOTE" ]; then
        echo "0"
      else
        echo $VERSION
      fi
    ;;
    -u|--update)
      git fetch origin
      LOCAL=$(git rev-parse @)
      REMOTE=$(git rev-parse origin/main)
      VERSION=$(git describe --tags $(git rev-list --tags --max-count=1))
      git pull
    ;;
    *)
      echo "Unknown option: $arg"
    ;;
  esac
  shift
done