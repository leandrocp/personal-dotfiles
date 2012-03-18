ZSH=$HOME/.oh-my-zsh
ZSH_THEME="gentoo"

source $ZSH/oh-my-zsh.sh
source $HOME/.zsh/config
source $HOME/.zsh/plugins
source $HOME/.zsh/aliases
source $HOME/.export

[[ -f ~/.localrc ]] && . ~/.localrc
