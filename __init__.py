from anki import hooks
from anki.decks import DeckManager
from aqt import mw
from aqt.utils import showInfo, qconnect
from aqt.qt import QAction, QCheckBox, QHBoxLayout
from anki.notes import Note
from aqt.qt import *
from aqt.gui_hooks import profile_did_open



def show_deck_menu():
    decks = mw.col.decks.all_names_and_ids()
    
    dialog = QDialog(mw)
    dialog.setWindowTitle("Select Decks")
    layout = QVBoxLayout(dialog)
    
    deck_checkboxes = []
    
    boxes_that_should_be_checked = check_deck()
    
    for deck in decks:
        if(deck.name[0] == "!"):
            continue
        checkbox = QCheckBox(deck.name)
        layout.addWidget(checkbox)
        if(deck.name in boxes_that_should_be_checked):
            checkbox.setChecked(True)
            checkbox.setDisabled(True)
        deck_checkboxes.append((deck, checkbox))
        
    button_layout = QHBoxLayout()
    
    confirm_button = QPushButton("Save")
    cancel_button = QPushButton("Exit")
    refresh_button = QPushButton("Refresh")
    
    button_layout.addWidget(confirm_button)
    button_layout.addWidget(cancel_button)
    button_layout.addWidget(refresh_button)
    
    layout.addLayout(button_layout)
    
    def on_cancel():
        mw.reset() 
        dialog.reject()
        

    def on_save():
        
        for touples in deck_checkboxes:
            deckname = touples[0].name
            if(not touples[1].isChecked() or not touples[1].isEnabled()):
                continue
            
            if " " in deckname:
                showInfo("Please remove all spaces from the name of the deck")
                continue
            
            card_ids = mw.col.find_cards(f"deck:{deckname}")
            
            back = []
            front = []
            
            for cardid in card_ids:
                card = mw.col.get_card(cardid)
                back.append(card.note()["Back"])
                front.append(card.question())
            
            make_deck(deckname, front, back)
            showInfo("Fliped deck: '" + deckname + "' successfully")
        mw.reset() 
        dialog.close()
    
    def on_refresh():
        Update()
            
    cancel_button.clicked.connect(on_cancel)
    confirm_button.clicked.connect(on_save)
    refresh_button.clicked.connect(on_refresh)
    
    dialog.exec()
  
#Input of deck name, Front of the cards being copied into the new deck, Back of the cards being copied into the new deck
#Creates a deck with the name of the deck being ![deckname]! and the cards in the deck being the reverse of the original deck
def make_deck(deck_name, front, back):
    newName = "!" + deck_name + "!"
    
    deck_id = mw.col.decks.id(newName)
    
    model = mw.col.models.by_name("Basic")

    for i in range(len(front)):
        note = Note(mw.col, model)
        
        note.fields[0] = back[i]
        note.fields[1] = front[i]
        
        mw.col.add_note(note, deck_id)
        

#Searches all decks for ![deckname]!. Returns a list of all decks that have this
def check_deck():
    decks = mw.col.decks.all_names_and_ids()
    
    ret = []
    
    for deck in decks:
        if(deck.name[0] == "!" and deck.name[-1] == "!"):
            ret.append(deck.name[1:-1])
    return ret


#function to update everything when the application starts or for some other reason
#if the deck counts and all the cards are the same not change
#if the flip deck has different cards the flip deck has to be updated to match the old one
def Update():
    flip_decks = check_deck()
        
    for deck in flip_decks:
        compare_decks(deck, "!" + deck + "!")
        showInfo(f"{deck} updated")
        
#compares the 2 decks and changes the flip deck to match the regular deck
def compare_decks(regular_deck, flip_deck):
    card_ids_regular = mw.col.find_cards(f"deck:{regular_deck}")
    
    flip_deck_id = mw.col.decks.id(flip_deck)
    
    regular_card_touple = []
    regular_card_names = []
    
    for card in card_ids_regular:
        RegCard = mw.col.get_card(card)
        regular_card_touple.append((RegCard.note()["Back"], RegCard.note()["Front"]))
        regular_card_names.append(RegCard.note()["Back"])

    
    card_ids_flip = mw.col.find_cards(f"deck:{flip_deck}")
    
    flip_card_touple = []
    flip_card_names = []
    
    for card in card_ids_flip:
        FlipCard = mw.col.get_card(card)
        flip_card_touple.append((FlipCard.note()["Front"], card))
        flip_card_names.append(FlipCard.note()["Front"])
    
    
    #After all similar cards are removed
    #The ones that needs to be removed from the flip deck are the left over cards after common cards from flip are removed
    #The cards that needs to be added to theflip deck are the left over cards after the common from the normal deck are removed
    needRemoval = [item for item in flip_card_names if item not in regular_card_names]
    addsAddition = [item for item in regular_card_names if item not in flip_card_names]
    
    model = mw.col.models.by_name("Basic")
    
    for item in addsAddition:
        note = Note(mw.col, model)
               
        note.fields[0] = item
        note.fields[1] = find_value_in(item, regular_card_touple)
        
        mw.col.add_note(note, flip_deck_id)
        
    for item in needRemoval:
        card_id = find_value_in(item, flip_card_touple)
        card = mw.col.get_card(card_id)
        note = card.note()
        mw.col.remove_notes([note.id])
        
    mw.reset()
        
#input of search key and the touple, 
#If the input is the regular touple, returns the back of the card, 
#if the input is the flip touple, it returns the card id.
def find_value_in(search, list_of_touples):
    for tup in list_of_touples:
        if(tup[0] == search):
            return tup[1]

def flip_deck_button():
    action = QAction("Deck Flipper", mw)
    action.triggered.connect(show_deck_menu)
    mw.form.menuTools.addAction(action) 

flip_deck_button()
profile_did_open.append(Update)