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
    print(f"xml_paths: {xml_paths}")
    print(f"output_midi_path: {output_midi_path}")
    """
    将多个 MusicXML 文件合并为一个 MIDI 文件。

    参数：
    - xml_paths: MusicXML 文件路径列表
    - output_midi_path: 输出的 MIDI 路径
    - instrument_name: 如果指定，将强制所有声部使用这个乐器
    """
    combined_score = stream.Score()

    for xml_path in xml_paths:
        print(xml_path)
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

def synthesize_all_sheets_to_mp3(xml_paths, output_mp3_path, soundfont_path="data/FluidR3_GM.sf2"):
    """
    将多个乐谱文件合成为一个MP3文件

    参数：
    - xml_paths: MusicXML 文件路径列表
    - output_mp3_path: 输出的 MP3 路径
    - soundfont_path: 音色库路径
    """
    import os
    import tempfile

    try:
        # 创建临时MIDI文件
        temp_midi = tempfile.mktemp(suffix='.mid')

        # 合并所有乐谱为MIDI
        merge_musicxml_to_midi(xml_paths, temp_midi)

        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_mp3_path), exist_ok=True)

        # 转换为MP3
        midi_to_mp3(temp_midi, output_mp3_path, soundfont_path)

        # 清理临时文件
        if os.path.exists(temp_midi):
            os.remove(temp_midi)

        return True

    except Exception as e:
        print(f"❌ 合成MP3失败: {e}")
        return False

def synthesize_single_sheet_to_mp3(xml_path, output_mp3_path, instrument_name=None, soundfont_path="data/FluidR3_GM.sf2"):
    """
    将单个乐谱文件生成为MP3文件

    参数：
    - xml_path: MusicXML 文件路径
    - output_mp3_path: 输出的 MP3 路径
    - instrument_name: 乐器名称，如果为None则保持原有乐器
    - soundfont_path: 音色库路径

    返回：
    - bool: 生成是否成功
    """
    import os
    import tempfile

    temp_midi = None
    try:
        # 详细验证输入文件
        if not os.path.exists(xml_path):
            print(f"❌ 乐谱文件不存在: {xml_path}")
            return False

        if os.path.getsize(xml_path) == 0:
            print(f"❌ 乐谱文件为空: {xml_path}")
            return False

        # 验证音色库文件
        if not os.path.exists(soundfont_path):
            print(f"❌ 音色库文件不存在: {soundfont_path}")
            return False

        # 创建临时MIDI文件
        temp_midi = tempfile.mktemp(suffix='.mid')
        print(f"🔄 开始处理: {xml_path} -> {output_mp3_path}")

        # 转换为MIDI
        print(f"🎼 转换MusicXML为MIDI...")
        musicxml_to_midi2(xml_path, temp_midi, instrument_name)

        # 验证MIDI文件是否生成成功
        if not os.path.exists(temp_midi) or os.path.getsize(temp_midi) == 0:
            print(f"❌ MIDI文件生成失败或为空")
            return False

        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_mp3_path), exist_ok=True)

        # 转换为MP3
        print(f"🎵 转换MIDI为MP3...")
        midi_to_mp3(temp_midi, output_mp3_path, soundfont_path)

        # 验证MP3文件是否生成成功
        if not os.path.exists(output_mp3_path):
            print(f"❌ MP3文件生成失败")
            return False

        if os.path.getsize(output_mp3_path) == 0:
            print(f"❌ MP3文件生成为空")
            return False

        # 验证MP3文件大小合理（至少1KB）
        mp3_size = os.path.getsize(output_mp3_path)
        if mp3_size < 1024:
            print(f"❌ MP3文件过小，可能生成异常: {mp3_size}字节")
            return False

        print(f"✅ MP3生成成功: {output_mp3_path} ({mp3_size/1024:.1f}KB)")
        return True

    except Exception as e:
        print(f"❌ MP3生成过程出错: {str(e)}")
        import traceback
        print(f"详细错误信息: {traceback.format_exc()}")
        return False

    finally:
        # 清理临时文件
        if temp_midi and os.path.exists(temp_midi):
            try:
                os.remove(temp_midi)
                print(f"🧹 清理临时MIDI文件: {temp_midi}")
            except:
                pass