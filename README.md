# Sampling-Theory Studio

## Table of Contents:
- [Description](#description)
- [Project Features](#project-features)
- [Quick Preview](#quick-preview)
- [Executing program](#executing-program)
- [Help](#help)
- [Contributors](#contributors)
- [License](#license)

## Description

The Sampling-Theory Studio is a desktop application designed to illustrate the signal sampling and recovery process, emphasizing the importance and validation of the Nyquist rate. The application allows users to load mid-length signals, visualize and sample them at different frequencies, and then recover the original signal using the Whittaker–Shannon interpolation formula. It also provides features for signal composition, additive noise introduction, real-time processing, and dynamic resizing.

## Project Features

- **Sample & Recover**:
  - Load a mid-length signal (around 1000 points).
  - Visualize and sample the signal at different frequencies.
  - Recover the original signal using Whittaker–Shannon interpolation.
  - Display three graphs: original signal with sampled points, reconstructed signal, and the difference between the original and reconstructed signals.

- **Load & Compose**:
  - Load signals from a file or compose signals using a signal mixer.
  - Signal mixer allows users to add multiple sinusoidal signals with different frequencies and magnitudes.
  - Users can remove components during signal composition.

- **Additive Noise**:
  - Introduce noise to the loaded signal with a custom/controllable Signal-to-Noise Ratio (SNR).
  - Demonstrate the dependency of noise effect on signal frequency.

- **Real-time**:
  - Sampling and recovery are performed in real-time upon user changes, eliminating the need for an explicit "Update" or "Refresh" button.

- **Resize**:
  - The application is easily resizable without affecting the user interface.

- **Different Sampling Scenarios**:
  - Prepare at least 3 testing synthetic signals, each addressing different scenarios.
  - Include a mix of 2Hz and 6Hz sinusoidals as an example.
  - Explore problematic scenarios or tricky features in the additional examples.

## Quick Preview

*Include screenshots or GIFs showcasing the application's interface and features.*

## Executing program

To be able to use our app, you can simply follow these steps:
1. Install Python3 on your device. You can download it from <a href="https://www.python.org/downloads/">Here</a>.
2. Install the required packages by the following command.
```
pip install -r requirements.txt
```
3. Run the file with the name "samplingStudioUI.py"

## Help

If you encounter any issues or have questions, feel free to reach out.

## Contributors

Gratitude goes out to all team members for their valuable contributions to this project.

<div align="left">
  <a href="https://github.com/cln-Kafka">
    <img src="https://avatars.githubusercontent.com/u/100665578?v=4" width="100px" alt="@Kareem Noureddine">
  </a>
  <a href="https://github.com/1MuhammadSami1">
    <img src="https://avatars.githubusercontent.com/u/139786587?v=4" width="100px" alt="@M.Sami">
  </a>
  <a href="https://github.com/MohamedSayedDiab">
    <img src="https://avatars.githubusercontent.com/u/90231744?v=4" width="100px" alt="@M.Sayed">
  </a>
</div>

## License

All rights reserved © 2023 to Team 19 - Systems & Biomedical Engineering, Cairo University (Class 2025)
