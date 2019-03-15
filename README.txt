
# TODO: better logging and error messages
# TODO: detect scenarios by looking at encounter sets which contain acts/agendas
# TODO: split off scenario sheet population as a separate script so we can run it
#       after the cards sheet has been completely filled in
# TODO: write test suite
# TODO: add mini cards for investigators
# TODO: documentation: in scenarios sheet don't try to add an encounter set associated with a specific scenario
# TODO: arkham_sheets.read_set should not set any values for blank cells
# TODO: figure out correct value for Unique field
# TODO: Split off card image creation, make a separate .o8c file
# TODO: update template

OCTGN package schema:

<OCTGN directory>
  Decks
    Arkham Horror - The Card Game
      <CampaignCode> - <CampaignName>
        <ScenarioNumber> - <ScenarioName>.o8d   # or for standalones, <StandaloneScenarioName> - <Version>.o8d
  GameDatabase
    a6d114c7-2e2a-4896-ad8c-0330605c90bf
      Decks
        <CampaignCode> - <CampaignName>
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

Scenarios are numbered as they are in the campaign guide, e.g. '1a - Extracurricular Activity'
