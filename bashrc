source $HOME/.bash/aliases
source $HOME/.bash/completions
source $HOME/.bash/config
source $HOME/.export

if [ -f ~/.localrc ]; then
  source ~/.localrc
fi
