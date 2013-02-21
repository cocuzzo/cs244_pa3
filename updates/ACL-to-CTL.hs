import CTL

-- Richer CTL syntax, compiled down to minimal representation

data CTLStateFormula = 
  CTLAtom NetworkElem
  | CTLStateConj CTLStateFormula CTLStateFormula
  | CTLStateDisj CTLStateFormula CTLStateFormula
  | CTLStateImpl CTLStateFormula CTLStateFormula
  | CTLStateNeg CTLStateFormula
  | CTLStateExists CTLPathFormula
  | CTLStateForAll CTLPathFormula
    
data CTLPathFormula =
  CTLNextTime CTLStateFormula
  | CTLEventually CTLStateFormula
  | CTLAlways CTLStateFormula
  | CTLUntil CTLStateFormula CTLStateFormula
    
reduceStateForm :: CTLStateFormula -> StateFormula
reduceStateForm cForm = 
  case cForm of
    CTLAtom a -> Atom a
    CTLStateConj a b -> StateConj (reduceStateForm a) (reduceStateForm b)
    CTLStateDisj a b -> StateNeg (StateConj 
                                  (StateNeg $ reduceStateForm a)
                                  (StateNeg $ reduceStateForm b))
    CTLStateImpl a b -> StateNeg $ StateConj (reduceStateForm a) (StateNeg $ reduceStateForm b)
    CTLStateNeg a -> StateNeg (reduceStateForm a)
    CTLStateExists a -> 
      case a of
        CTLAlways p -> StateNeg (StateForAll $ reducePathForm a)
        _ -> StateExists $ reducePathForm a
                             
    CTLStateForAll a -> 
      case a of
        CTLAlways p -> StateNeg (StateExists $ reducePathForm a)
        _ -> StateForAll $ reducePathForm a
    
reducePathForm :: CTLPathFormula -> PathFormula
reducePathForm cForm = 
  case cForm of
    CTLNextTime a -> NextTime $ reduceStateForm a
    CTLEventually a -> Until True (reduceStateForm a)
    CTLAlways a -> Until True (StateNeg $ reduceStateForm a)
    CTLUntil a b -> Until (reduceStateForm a) (reduceStateForm b)

-- In the future, this should really be IPs, but then we'd have to add that to the model
type AccessControlList = [(NetworkElem, NetworkElem, Bool)]

aclToCTL :: AccessControlList -> CTLStateFormula
-- Open or closed by default?
aclToCTL [] = True
aclToCTL (h1,h2,flag):acls = if flag then
                            CTLConj (CTLStateImpl (CTLAtom h1)
                                     (CTLStateExists $ CTLEventually (CTLAtom h2)))
                            (aclToCTL acls)
                          else 
                            CTLConj (CTLStateImpl (CTLAtom h1)
                                     (CTLStateNeg (CTLStateExists $ 
                                           CTLEventually (CTLAtom h2))))
                            (aclToCTL acls)