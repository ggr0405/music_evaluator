import inspect
from music21 import converter, stream, instrument
from midi2audio import FluidSynth
def get_instruments_from_score(file_path):
    """
    读取 MusicXML 文件，返回声部对应的乐器名称列表。
    如果某个声部没有明确乐器信息，返回 "Unknown"。
    """
    score = converter.parse(file_path)
    instruments = []
    for part in score.parts:
        instr = part.getInstrument(returnDefault=True)
        # 取乐器名，若无名称则用 instrumentName 属性，否则标记为 Unknown
        name = instr.partName or instr.instrumentName or "Unknown"
        if name.strip().lower() == 'voice':
            continue
        instruments.append(name)
    #return instruments

    all_instruments = [name for name, obj in inspect.getmembers(instrument)
                       if inspect.isclass(obj) and issubclass(obj, instrument.Instrument)]
    #return  all_instruments
    return ["Clarinet", "Trumpet", "Violin", "Cello", "Flute"]

def musicxml_to_midi(xml_path, midi_path, instrument_name='Piano'):
    score = converter.parse(xml_path)
    instr = getattr(instrument, instrument_name)()
    for part in score.parts:
        part.insert(0, instr)
    score.write('midi', fp=midi_path)


def musicxml_to_midi2(xml_path, midi_path, instrument_name=None):
    score = converter.parse(xml_path)

    if instrument_name is not None:
        instr = getattr(instrument, instrument_name)()
        for part in score.parts:
            # 清除已有乐器，插入新的乐器
            for el in part.getElementsByClass(instrument.Instrument):
                part.remove(el)
            part.insert(0, instr)

    # instrument_name == None 时，不做任何修改，合成全部声部

    score.write('midi', fp=midi_path)


def merge_musicxml_to_midi(xml_paths, output_midi_path, instrument_name=None):
    """
    将多个 MusicXML 文件合并为一个 MIDI 文件。

    参数：
    - xml_paths: MusicXML 文件路径列表
    - output_midi_path: 输出的 MIDI 路径
    - instrument_name: 如果指定，将强制所有声部使用这个乐器
    """
    combined_score = stream.Score()

    for xml_path in xml_paths:
        try:
            score = converter.parse(xml_path)

            if instrument_name is not None:
                instr = getattr(instrument, instrument_name)()
                for part in score.parts:
                    # 清除已有乐器，插入新的乐器
                    for el in part.getElementsByClass(instrument.Instrument):
                        part.remove(el)
                    part.insert(0, instr)

            # 将每个乐谱的所有 parts 合并到最终结果
            for part in score.parts:
                combined_score.append(part)

        except Exception as e:
            print(f"❌ 处理失败: {xml_path} - {e}")

    # 写出为 MIDI
    combined_score.write('midi', fp=output_midi_path)
    print(f"✅ 合并完成，输出文件：{output_midi_path}")


def midi_to_mp3(midi_path, mp3_path, soundfont_path):
    fs = FluidSynth(sound_font=soundfont_path)
    fs.midi_to_audio(midi_path, mp3_path)