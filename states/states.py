from aiogram.fsm.state import State, StatesGroup


class ImageGenStates(StatesGroup):
    waiting_for_prompt = State()


class TextGenStates(StatesGroup):
    waiting_for_prompt = State()


class TTSStates(StatesGroup):
    waiting_for_text = State()


class STTStates(StatesGroup):
    waiting_for_voice = State()


class AIChatStates(StatesGroup):
    chatting = State()
