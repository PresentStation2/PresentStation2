Installation steps:

	If there is no Python on the machine:
		Install Python (version 3.7-3.9, newer versions are not yet supported by all the required packages) 
			Windows: https://www.python.org/downloads/release/python-397/ (choose Windows installer and run as usual)
			Linux: https://docs.python-guide.org/starting/install3/linux/
			
		Check if Pip (Python package manager) is installed by writing: pip3 --version
		into the console (Win + cmd).
		If not, install from here:
			https://pip.pypa.io/en/stable/installation/
			
		Install required packages (versions are tested for python 3.7):
			List of needed packages is in the requirements.txt, use it as follows:
			pip3 install -r requirements.txt
		
FE_Setup.json:
	
	This is a configuration file for the feature extractor.
	It uses the FFmpeg software and needs to know its path on your computer.
	
	Windows:
		If you don't have FFmpeg installed, you don't need to do anything, default setting is "ffmpegPath": "FFmpeg", which uses enclosed ffmpeg from the local directory.
		If ffmpeg is already installed on the computer, "ffmpegPath": "" will use the your existing ffmpeg.
		If another version should be used, set ffmpegPath as path leading to ffmpeg.exe
	
	Linux:
		Install ffmpeg on the machine (e.g. https://linuxize.com/post/how-to-install-ffmpeg-on-debian-9/) and 
		Set "ffmpegPath": ""

Usage:
	
	Extractor actually filters inputs so it can only process .wav and .mp3 inputs.
	Extraction is done via FeatureExtractor.py, result is saved in TAB separated .txt file and 
	also creates a .log file (hopefully not needed), both in the directory with the soundfiles.
	Run the exctractor with a console command (Win + cmd).
	
	1) Use on single file:
		python FeatureExtractor.py fullPathToAFile/file.wav
	
	2) Use on a directory:
		python FeatureExtractor.py fullPathToADirectory
