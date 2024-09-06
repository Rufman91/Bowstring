# Bowstring
Small widget to import positional data and light microscope images from jpk spm desktop software for determination of bowstring
(Quigley 2016, https://doi.org/10.1371/journal.pone.0161951) geometry and parameters.


# Setting Up the Bowstring Environment

To compile and use the Bowstring widget in this repository, you will need to set up a specific Python environment called **Python38Bowstring**.
This environment ensures all necessary dependencies are met for building the application with `pyinstaller`.

## Step-by-Step Guide

1. **Download the YAML file:**  
   The environment YAML file, named `Python38Bowstring.yml`, is included in this repository. Download or clone this repository to get started.

2. **Create the Environment:**  
   Open your terminal or Anaconda Prompt and navigate to the directory where the `Python38Bowstring.yml` file is located. Then, run the following command to create the environment:

       conda env create -f Python38Bowstring.yml

   This command will set up a new environment named `Python38Bowstring` with all the necessary packages and dependencies.

3. **Activate the Environment:**  
   Once the environment is created, activate it using:

       conda activate Python38Bowstring

   Your terminal should now indicate that you are working within the `Python38Bowstring` environment.

## Compiling the Bowstring Widget

To use the contents of this repository, you will need to compile the `BowstringWidget.py` file into an executable. This requires `pyinstaller` to be run within the `Python38Bowstring` environment.

1. **Ensure You Are in the Correct Environment:**

       conda activate Python38Bowstring

2. **Compile the Widget:**  
   In your terminal, navigate to the directory where the `BowstringWidget.py` file is located, then use the following `pyinstaller` command to compile the `BowstringWidget.py` script:

       pyinstaller BowstringWidget.py --distpath <path/to/where/the/app/should/be>/dist --workpath <path/to/where/the/app/should/be>/build --add-data "<full/path/to/Bowstring/repository>/TestImage.jpg:." --add-data "<full/path/to/Bowstring/repository>/icons/:./icons"

   This will generate the necessary executable files to run the Bowstring widget application. You will then need to adjust the path to the BowstringWidget executable in the Bowstring.py script
   that will be opened within the JPK control softwares Experiment Planner.

## Additional Notes

- Ensure that all dependencies and Python versions are correctly managed by the `Python38Bowstring` environment.
- If you encounter any issues while setting up the environment or compiling the widget, please refer to the official Conda documentation or the PyInstaller documentation for troubleshooting steps.
