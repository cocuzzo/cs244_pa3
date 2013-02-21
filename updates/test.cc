#include <boost/bind.hpp>
#include "assert.h"
#include "component.hh"
#include "flow.h"
#include "packet-in.hh"
#include "vlog.hh"

#include "netinet++/ethernet.hh"

namespace {

  using namespace vigil;
  using namespace vigil::container;

  Vlod_module lg("test");

  class Rule
  {
  public:
    Flow flow;
    ofp_action_output action;
    Rule(Flow _flow, ofp_action_output _action) : Rule { }
  };
}
