import pyaudio
import sys

def test_audio_setup():
    """Test PyAudio setup and devices"""
    
    print("🔧 PyAudio Device Test")
    print("=" * 30)
    
    try:
        audio = pyaudio.PyAudio()
        
        #print(f"PyAudio version: {pyaudio.get_version_text()}")
        #print(f"Device count: {audio.get_device_count()}")
        
        print("\n📱 Available Devices:")
        print("-" * 40)
        
        input_devices = []
        output_devices = []
        
        for i in range(audio.get_device_count()):
            try:
                info = audio.get_device_info_by_index(i)
                device_name = info['name']
                
                if info['maxInputChannels'] > 0:
                    input_devices.append((i, device_name))
                    print(f"🎤 INPUT  {i}: {device_name}")
                
                if info['maxOutputChannels'] > 0:
                    output_devices.append((i, device_name))
                    print(f"🔊 OUTPUT {i}: {device_name}")
                    
            except Exception as e:
                print(f"❌ Device {i}: Error - {e}")
        
        print("-" * 40)
        
        # Test default devices
        try:
            default_input = audio.get_default_input_device_info()
            print(f"✅ Default input: {default_input['name']}")
        except OSError:
            print("❌ No default input device")
        
        try:
            default_output = audio.get_default_output_device_info()
            print(f"✅ Default output: {default_output['name']}")
        except OSError:
            print("❌ No default output device")
        
        audio.terminate()
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if not input_devices:
            print("❌ No input devices found. Please connect a microphone.")
            print("   - Check if microphone is connected")
            print("   - Update audio drivers")
            print("   - Try running as administrator")
        else:
            print("✅ Input devices available for recording")
        
        if not output_devices:
            print("❌ No output devices found.")
        else:
            print("✅ Output devices available for playback")
            
        return len(input_devices) > 0
        
    except Exception as e:
        print(f"❌ PyAudio error: {e}")
        print("\n🔧 Installation tips:")
        print("Windows: pip install pipwin && pipwin install pyaudio")
        print("macOS: brew install portaudio && pip install pyaudio")
        print("Linux: sudo apt-get install portaudio19-dev && pip install pyaudio")
        return False

if __name__ == "__main__":
    if test_audio_setup():
        print("\n✅ Audio setup looks good!")
        sys.exit(0)
    else:
        print("\n❌ Audio setup needs attention")
        sys.exit(1)
