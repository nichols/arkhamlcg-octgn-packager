# common functions used across the whole package

import re
import attr
import uuid


_url_regex = re.compile(r"^(?:http(s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$")
_uuid_regex = re.compile(r"^[0-9a-f]{8}(?:-?[0-9a-f]{4}){3}-?[0-9a-z]{12}$")

_set_types = frozenset(
    ['Core Set', 'Expansion', 'Mythos Pack', 'Scenario Pack', 'Promo', 'Other'])

_player_card_types = frozenset(
    ['Asset', 'Skill', 'Event', 'Investigator'])
_encounter_card_types = frozenset(
    ['Agenda', 'Act', 'Location', 'Treachery', 'Enemy', 'Story'])
_all_card_types = frozenset.union(_player_card_types, _encounter_card_types)

_card_classes = frozenset(
    ['Guardian', 'Seeker', 'Rogue', 'Mystic', 'Survivor', 'Neutral', 'Mythos'])
_asset_slots = frozenset(
    ['Body', 'Hand', 'Arcane', 'Accessory', 'Ally', 'Tarot'])


_uuid_str_factory = lambda : "{}".format(uuid.uuid4())

# Reusable attr.s-style validators.
def _is_valid_uuid(self, attribute, value):
    if not _uuid_regex.match(value):
        raise ValueError("Invalid UUID {}.".format(value))

def _is_valid_url(self, attribute, value):
    if not _url_regex.match(value):
        raise ValueError("Invalid URL {}.".format(value))

def _nonempty_string(s):
    if s is None:
        return None
    return str(s).strip() or None

# Most fields are supposed to be a nonempty string or None.
_attr_string_or_none = lambda: attr.ib(
    type=str, default=None, converter=_nonempty_string)
_attr_int_or_none = lambda: attr.ib(
    type=int, default=None, converter=attr.converters.optional(int))


@attr.s(frozen=True, kw_only=True)
class CardFace:
    # Required fields
    # TODO: support empty image_url for cards with missing images, add warning
    image_url = attr.ib(type=str, validator=_is_valid_url)

    # Fields that should be required, except that cardgamedb doesn't have these
    # fields for back sides.
    Name = _attr_string_or_none()
    Type = attr.ib(type=str, default=None,
                   validator=attr.validators.optional(
                       attr.validators.in_(_all_card_types)))

    # optional fields
    Subtitle = _attr_string_or_none()
    Subtype = _attr_string_or_none()
    Traits = attr.ib(type=list, factory=list)
    Text = _attr_string_or_none()
    Health = _attr_string_or_none()    # Health for investigators, assets, and enemies
    Sanity = _attr_string_or_none()    # Sanity for investigators and assets
    # underscore suffix because 'class' is a python keyword
    Class = attr.ib(type=str, default=None,
                    validator=attr.validators.optional(
                        attr.validators.in_(_card_classes)))
    Level = _attr_string_or_none()     # Level for player cards, agenda/act number for agendas/acts
    Cost = _attr_string_or_none()
    Willpower = _attr_int_or_none() # Skill for investigators, skill icon on other player cards
    Intellect = _attr_int_or_none() # Skill for investigators, skill icon on other player cards
    Combat = _attr_int_or_none()    # Skill for investigators, skill icon on other player cards, fight difficulty for enemies
    Agility = _attr_int_or_none()   # Skill for investigators, skill icon on other player cards, evade difficulty for enemies
    Wild = _attr_int_or_none()      # Skill icon for player cards. Not used in OCTGN for some reason
    Slot = _attr_string_or_none()
    Unique = attr.ib(type=bool, default=False, converter=bool)
    Shroud = _attr_int_or_none()
    Clues = _attr_string_or_none()
    Doom = _attr_string_or_none()
    Damage = _attr_int_or_none()
    Horror = _attr_int_or_none()
    VictoryPoints = _attr_int_or_none()

    # Health, Clues, Doom all might have [Investigators] symbol
    # Text might have those + others


@attr.s(frozen=True, kw_only=True)
class Card:
    # Required fields.
    number = attr.ib(type=int,
                     converter=int)
    front = attr.ib(type=CardFace,
                    validator=attr.validators.instance_of(CardFace))

    # Optional fields.
    id = attr.ib(type=str,
                 factory=_uuid_str_factory,
                 validator=_is_valid_uuid)
    quantity = attr.ib(type=int, default=1, converter=int)

    # double-sided only
    back = attr.ib(type=CardFace,
                   default=None,
                   validator=attr.validators.optional(
                        attr.validators.instance_of(CardFace)))

    # encounter cards only
    encounter_set = _attr_string_or_none()


    @classmethod
    def from_cardgamedb(cls, card_dict):
        kwargs = dict(
            set_number=card_dict['Number'],
            encounter_set=card_dict.get('Encounter Set'),
            quantity=card_dict['Quantity'],
            back=None,
            front=CardFace(
                image_url=card_dict['imgs'][0],
                Name=card_dict['cardTitle'],
                Type=card_dict['Type'],
                Subtitle=card_dict.get('Subtitle'),
                Subtype=card_dict.get('Subtype'),
                Traits=card_dict['traits'],
                Text=card_dict['gameTexts'][0],
                Health=card_dict.get('Health'), # Both player cards and enemies.
                Sanity=card_dict.get('Sanity'),
                Class_=card_dict.get('Class'),
                Level=card_dict.get('Level'),
                Cost=card_dict.get('Cost'),
                Willpower = card_dict.get('Willpower'),
                Intellect = card_dict.get('Intellect'),
                Combat = card_dict.get('Combat'),
                Agility = card_dict.get('Agility'),
                Wild = card_dict.get('Wild'),
                Slot = card_dict.get('Slot'),
                Unique = card_dict['unique'],
                Shroud = None,  # Not supported by cardgamedb
                Clues = None,   # Not supported by cardgamedb
                Doom = card_dict.get('Doom Threshold'),
                Damage = card_dict.get('Damage'),
                Horror = card_dict.get('Horror'),
                Victory = card_dict.get('Victory'),
            )
        )
        if len(card_dict['imgs']) > 1:  # Card is double-sided
            kwargs['back'] = CardFace(
                image_url=card_dict['imgs'][1],
                Text=card_dict['gameTexts'][1],
            )
        return cls(**kwargs)


def _is_list_of_cards(self, attribute, value):
    for card in value:
        if not isinstance(card, Card):
            raise ValueError("Invalid object in cards list: {}".format(card))

@attr.s(kw_only=True)
class CardSet:
    name = attr.ib(type=str, converter=_nonempty_string)
    type = attr.ib(type=str, validator=attr.validators.in_(_set_types))
    id = attr.ib(type=str, factory=_uuid_str_factory, validator=_is_valid_uuid)
    cards = attr.ib(type=list, factory=list, validator=_is_list_of_cards)

    @classmethod
    def from_cardgamedb(cls, set_dict):
        set_dict['cards'] = [
            Card.from_cardgamedb(card) for card in set_dict['cards']]
        return cls(**set_dict)
