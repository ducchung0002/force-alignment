from predict import handle_sample, load_model
import subprocess
import json
import torchaudio
import argparse
import string
import uuid


def process_vietnamese_string(input_str):
    # Convert to lowercase
    lower_str = input_str.lower()

    # Remove punctuation
    no_punctuation_str = ''.join(
        char for char in lower_str if char not in string.punctuation)

    # Remove extra spaces (optional)
    cleaned_str = ' '.join(no_punctuation_str.split())

    return cleaned_str
    cut_output_path = f"{uuid.uuid4().hex}.mp3"
    resample_output_path = f"{uuid.uuid4().hex}.wav"

    print('audio', audio)
    print('cut_output_path', cut_output_path)
    print('resample_output_path', resample_output_path)

    command = [
        "ffmpeg",
        "-i", audio,
        "-ss", f"{start:.3f}",  # Format to 3 decimal places
        "-t", f"{duration:.3f}",
        "-c", "copy",
        cut_output_path
    ]

    # Run the command
    subprocess.run(command, check=True)

    command = [
        "ffmpeg",
        "-i", cut_output_path,  # Input file
        "-ar", "16000",  # Set audio sample rate to 16 kHz
        "-ac", "1",  # Set audio channels to mono
        resample_output_path  # Output file
    ]

    # Run the command
    subprocess.run(command, check=True)

    # os.remove(cut_output_path)  # Remove the temporary file
    return resample_output_path


if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser()

    # Add arguments
    parser.add_argument("--audio", type=str, required=True)
    parser.add_argument("--lyric", type=str, required=True)
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--out", type=str, required=True)

    # Parse the arguments
    args = parser.parse_args()

    audio = args.audio
    lyric = args.lyric
    start = args.start
    output_path = args.out
    # Load the audio file
    waveform, sr = torchaudio.load(audio)

    # Resample to 16kHz
    if sr != 16000:
        resampler = torchaudio.transforms.Resample(
            orig_freq=sr,
            new_freq=16000
        )
        waveform = resampler(waveform)

    with open(lyric, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # Remove newline characters and print each line
    lines = [line.strip() for line in lines]
    lyric_json = []
    for lyric_sentence in lines:
        sentence = process_vietnamese_string(lyric_sentence)
        word_objects = [{"s": 0, "e": 0, "d": word}
                        for word in sentence.split(' ')]
        lyric_json.append({"s": 0, "e": 0, "l": word_objects})

    load_model()
    lyric_alignment = handle_sample(waveform, lyric_json)
    custom_json = []
    for lyric in lyric_alignment:
        # sentence = {
        #     "start_time": lyric['s'] + start,
        #     "end_time": lyric['e'] + start,
        #     "words": [
        #         {"start_time": lr['s'] + start,
        #             "end_time": lr['e'] + start, "word": lr['d']}
        #         for lr in lyric['l']
        #     ]
        # }
        custom_json.append([{
            "start_time": lr['s'] + start,
            "end_time": lr['e'] + start,
            "word": lr['d']
        } for lr in lyric['l']])


    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(custom_json, file, ensure_ascii=False)
