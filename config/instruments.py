"""
全局乐器配置文件
定义系统中所有乐器选择相关的配置
"""

# 系统支持的乐器列表（用于前端显示）
INSTRUMENT_CHOICES = ["合声", "Piano", "Clarinet", "Trumpet", "Violin", "Violoncello", "Flute"]

# 仅用于MIDI处理的乐器列表（不包含"合声"）
MIDI_INSTRUMENTS = ["Piano", "Clarinet", "Trumpet", "Violin", "Violoncello", "Flute"]

# 乐器映射（如果需要将显示名称映射到music21库名称）
INSTRUMENT_MAPPING = {
    "Piano": "Piano",
    "Clarinet": "Clarinet",
    "Trumpet": "Trumpet",
    "Violin": "Violin",
    "Violoncello": "Violoncello",  # music21中大提琴的正确名称
    "Flute": "Flute"
}

def get_instrument_choices():
    """获取所有乐器选择（包含合声）"""
    return INSTRUMENT_CHOICES.copy()

def get_midi_instruments():
    """获取MIDI处理支持的乐器列表（不包含合声）"""
    return MIDI_INSTRUMENTS.copy()

def get_music21_instrument_name(display_name):
    """获取music21库中对应的乐器类名"""
    return INSTRUMENT_MAPPING.get(display_name, display_name)