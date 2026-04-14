if [ -r /run/ghostship/internal.env ]; then
  . /run/ghostship/internal.env
  export _GHOSTSHIP_ROUTER_API_KEY
fi
