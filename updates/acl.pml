/* ACL example from HotNets paper */

/* Blackhat, whitehat, I, F1-3, Server */

mtype = { web, any };

chan Bp1_Ip1 = [4] of { mtype };
chan Bp2_Ip2 = [4] of { mtype };
chan Wp1_Ip3 = [4] of { mtype };
chan Wp2_Ip4 = [4] of { mtype };

chan Ip5_F1p1 = [4] of { mtype };
chan Ip6_F2p1 = [4] of { mtype };
chan Ip7_F3p1 = [4] of { mtype };

chan F_S = [8] of { mtype };

chan C_I = [0] of { bool };
chan C_F1 = [0] of { bool };
chan C_F2 = [0] of { bool };
chan C_F3 = [0] of { bool };

proctype filter_switch(chan in_chan, out_chan/* , controller */; bool filter)
{
    do
      :: in_chan?web -> out_chan!web
      :: in_chan?any -> if
		     :: (filter) -> skip
		     :: (!filter) -> out_chan!any
		   fi
      /* :: controller?filter */
    od
}

active proctype ingress()
{
  mtype msg;
  do
    :: Bp1_Ip1?msg -> Ip5_F1p1!msg
    :: Bp2_Ip2?msg -> Ip5_F1p1!msg
    :: Wp1_Ip3?msg -> Ip6_F2p1!msg
    :: Wp2_Ip4?msg -> Ip7_F3p1!msg
    /* :: C_I?x -> goto update */
  od;
  
/* update: */
/*   do */
/*     :: Bp1_Ip1?msg -> Ip5_F1p1!msg */
/*     :: Bp2_Ip2?msg -> Ip6_F2p1!msg */
/*     :: Wp1_Ip3?msg -> Ip7_F3p1!msg */
/*     :: Wp2_Ip4?msg -> Ip7_F3p1!msg */
/*   od */
}

/* active proctype controller() */
/* { */
  
/* } */

active proctype Blackhat()
{
  do
    :: Bp1_Ip1!web
    :: Bp1_Ip1!any
    :: Bp2_Ip2!web
    :: Bp2_Ip2!any       
  od
}

active proctype Whitehat()
{
  do
    :: Wp1_Ip3!web
    :: Wp1_Ip3!any
    :: Wp2_Ip4!web
    :: Wp2_Ip4!any       
  od
}

init
{
  /* F1 */
  run filter_switch(Ip5_F1p1, F_S, true);
  /* F2 */
  run filter_switch(Ip6_F2p1, F_S, false);
  /* F3 */
  run filter_switch(Ip7_F3p1, F_S, false)  
}