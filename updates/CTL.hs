import Data.List
import Data.Number.PartialOrd

data NetworkElem = Switch Int | Host Int deriving Show

data Location = Port Int | Flood deriving Show

-- Graph is a labeled multi-graph

type Graph = [((NetworkElem, Location), (NetworkElem, Location))]

data Pattern = Pattern {in_port :: Maybe Int, 
                      dl_src :: Maybe Int,
                      dl_dst :: Maybe Int,
                      dl_type :: Maybe Int,
                      nw_src :: Maybe Int,
                      nw_dst :: Maybe Int,
                      nw_proto :: Maybe Int,
                      tp_src :: Maybe Int, 
                      tp_dst :: Maybe Int} deriving (Show, Eq)

-- Is there a way to get this programmatically?

patternAccessors = [ in_port,
                      dl_src,
                      dl_dst,
                      dl_type,
                      nw_src,
                      nw_dst,
                      nw_proto,
                      tp_src,
                      tp_dst  ]

instance PartialOrd (MaybeInt) where
  cmp Nothing Nothing = Just EQ
  cmp Nothing (Just _) = Just GT
  cmp (Just _) Nothin = Just LT
  cmp (Just a) (Just b) = if a == b then Just EQ else Nothing

meet :: Maybe Ordering -> Maybe Ordering -> Maybe Ordering
meet Ord1 Ord2 = case (Ord1, Ord2) of
  (Just EQ, Just EQ) -> Just EQ
  (Just EQ, Just LT) -> Just LT
  (Just EQ, Just GT) -> Just GT
  (Just LT, Just EQ) -> Just LT
  (Just LT, Just LT) -> Just LT
  (Just GT, Just EQ) -> Just GT
  (Just GT, Just GT) -> Just GT
  _ -> Nothing
              
instance PartialOrd Pattern where
  cmp (Pattern a) (Pattern b) =
    foldl meet (Just EQ) 
     (map (\accessor -> cmp (accessor a) (accessor b)) patternAccessors)
    
data Action = Drop | Forward Location
            deriving Show

data Rule = Rule {pattern :: Pattern, action :: Action} deriving (Show)
instance Eq Rule where
  Rule {pattern=p} == Rule {pattern=p'} = (p == p')
instance PartialOrd Rule where
  cmp (Rule {pattern=p}) (Rule {pattern=p'}) = cmp p p'
  
type Configuration = [Rule]
  
type NetworkConfiguration = [(NetworkElem, Configuration)]

-- For the first abstraction, the only properties we specify are simply paths in the graphs, i.e. sequences of networkelements

data StateFormula =
  True
  | False
  | Atom NetworkElem
  | StateConj StateFormula StateFormula
  | StateNeg StateFormula
  | StateExists PathFormula
  | StateForAll PathFormula
    

data PathFormula =
  NextTime StateFormula
  | Until StateFormula StateFormula
  -- -- Re-enable for CTL*
  -- StateForm StateFormula
  -- | PathConj PathFormula
  -- | PathNeg PathFormula
  -- | NextTime PathFormula
  -- | Until PathFormula PathFormula
    
-- The configuration will tell us how to abstract out the irrelevant fields. For now, just treat every state abstractly
type State = Int

-- First iteration: abstract graph as non-multigraph
type ReachabilityRelation = [(State, State)]

type Label = State -> [NetworkElem]

type TemporalStructure = ([State], ReachabilityRelation)


