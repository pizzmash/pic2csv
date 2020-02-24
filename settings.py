# coding: UTF-8
import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

AP = os.environ.get("API_KEY")
MIN_W = int(os.environ.get("MIN_W"))
MIN_H = int(os.environ.get("MIN_H"))
EXP_X = int(os.environ.get("X_EXPANSION"))
EXP_Y = int(os.environ.get("Y_EXPANSION"))
NOISE_CHARS = os.environ.get("NOISE_CHARACTORS")
