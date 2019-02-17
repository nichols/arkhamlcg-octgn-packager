
# Input: JSON file containing metadata for a set of cards, including URLs of card images
# Creates necessary directories and files to load this set into OCTGN

"""
OCTGN package schema:

<OCTGN directory>
  Decks
    Arkham Horror - The Card Game
      <SetNumber> - <SetName>
        <ScenarioNumber> - <ScenarioName>.o8d   # or for standalones, <StandaloneScenarioName> - <Version>.o8d
  GameDatabase
    a6d114c7-2e2a-4896-ad8c-0330605c90bf
      Decks
        <SetNumber> - <SetName>
          <ScenarioNumber> - <ScenarioName>.o8d 
      Sets
        <SetGUID>
          set.xml                               # XML file with metadata for all cards in this set
  ImageDatabase
    a6d114c7-2e2a-4896-ad8c-0330605c90bf
      Sets
        <SetGUID>
          Cards
            <CardGUID>.jpg
            <CardGUID>.b.jpg    # reverse side
            <CardGUID>.png      # PNGs are OK too

"""
