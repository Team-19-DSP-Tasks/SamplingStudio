from PyQt5.QtWidgets import QApplication, QFileDialog
import pandas as pd
import pyqtgraph as pg
import numpy as np
import os
from scipy.interpolate import interp1d
import json

class Loaded_Signal:
    def __init__(self, file_path):
        self.file_path = file_path
        self.file_name = os.path.basename(self.file_path)

class Composed_Signal:
    def __init__(self):
        self.amplitude = 0
        self.frequency = 0
        self.phase = 0
        self.composed_signals = {}

class SignalProcessor(Loaded_Signal, Composed_Signal):
    def __init__(self, ui, file_path):
        super().__init__(file_path)
        self.ui = ui
        self.column = None

        #parameters for two signal types
        self.max_freq = 0
        self.sampling_period = 0
        self.sampling_frequency = 0
        self.signal_duration = 0
        self.sample_points = 0

        #sampling points coordinates
        self.markers_x = []
        self.markers_y = []

        #Initialize here to keep track of data and not overwrite the composed signal data on the dictionary with every call
        self.added_signal = Composed_Signal()

        #Loaded Signal Connections
        self.ui.actionExit.triggered.connect(lambda: QApplication.quit())
        self.ui.actionOpen_Signal.triggered.connect(self.import_signal)
        self.ui.fmax_ratio_slider.setRange(0, 8)

        #Composed Signal Connections
        self.ui.add_signal_btn.clicked.connect(self.compose_signal)
        self.ui.delete_signal_btn.clicked.connect(self.delete_selected_signal)
        self.ui.save_ex_btn.clicked.connect(self.save_composed_signals_action)
        self.ui.load_ex_btn.clicked.connect(self.load_composed_signals_action)
        self.ui.noise_slider.valueChanged.connect(self.switch_function)

        # Connect the valueChanged signals of the sliders to the sample_and_update method of the correct signal
        self.ui.fmax_ratio_slider.valueChanged.connect(self.switch_function)

    def update_plot(self, plot, x_data, y_data, name):
        if plot.plotItem.legend is None:
            plot.plotItem.addLegend()
        if len(plot.listDataItems()) == 0:
            plot.plot(x_data, y_data, name=name)
        else:
            # Find the item with the specified name and update its data
            for item in plot.listDataItems():
                if item.name() == name:
                    item.setData(x_data, y_data)
                    break
        plot.plotItem.legend.setVisible(True)

    def reset_slider(self):
        self.ui.fmax_ratio_slider.setValue(0)
        self.ui.fs_number_label.setText('0' + 'Hz')
        self.ui.fmax_ratio_label.setText('0' + 'x')

    def switch_function(self, use_composed_signal):
        self.use_composed_signal = use_composed_signal
        # Disconnect both sliders
        self.ui.fmax_ratio_slider.valueChanged.disconnect()
        self.ui.noise_slider.valueChanged.disconnect()

        if self.use_composed_signal != True:
            # When using a composed signal, connect only the noise_slider to compose_signal
            self.ui.noise_slider.valueChanged.connect(self.sampled_composed_signal)
            self.ui.fmax_ratio_slider.valueChanged.connect(self.sampled_composed_signal)

        else:
                # When not using a composed signal (imported file or sampling), connect the fmax_ratio_slider to sample_signal
                self.ui.fmax_ratio_slider.valueChanged.connect(self.sample_signal)
                self.ui.noise_slider.valueChanged.connect(self.sample_signal)

    def add_noise_to_signal(self, signal, snr):
        # Calculate the signal power
        signal_power = np.var(signal)

        # Calculate the noise power based on the desired SNR
        snr = 10 ** (snr / 10)  # Convert SNR from dB to linear scale
        noise_power = signal_power / snr

        # Generate noise with the same length as the signal
        noise = np.random.normal(0, np.sqrt(noise_power), len(signal))

        # Add the noise to the signal
        noisy_signal = signal + noise

        return noisy_signal

#Loaded Signal Functions
    def import_signal(self):
        self.use_composed_signal = True
        self.switch_function(self.use_composed_signal)
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(None, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)", options=options)
        self.Signal = Loaded_Signal(file_path)
        imported_signal = pd.read_csv(self.Signal.file_path)
        self.calc_parameters(imported_signal)

        # Clear the old signal data and plots
        self.ui.graph_1.clear()
        self.ui.graph_2.clear()
        self.ui.graph_3.clear()
        self.reset_slider()
        self.update_plot(self.ui.graph_1, imported_signal['time'], imported_signal['values'], name=self.Signal.file_name)

    def calc_parameters(self, signal):
        self.sampling_period = signal['time'].diff().mean()
        self.sampling_frequency = 1 / self.sampling_period
        self.max_freq = self.sampling_frequency / 2
        self.signal_duration = signal['time'].max() - signal['time'].min()

    def sample_signal(self):
        self.use_composed_signal = True
        self.switch_function(self.use_composed_signal)
        fmax_ratio_slider_value = self.ui.fmax_ratio_slider.value()

        if hasattr(self, 'Signal'):
            imported_signal = pd.read_csv(self.Signal.file_path)
            self.calc_parameters(imported_signal)

            self.markers_x = []
            self.markers_y = []

            # Check if the noise_slider has changed
            if self.ui.noise_slider.isSliderDown():
                noisy_signal = self.add_noise_to_signal(imported_signal['values'], self.ui.noise_slider.value())
                self.update_plot(self.ui.graph_1, imported_signal['time'], noisy_signal, name=self.Signal.file_name)
            else:
                # if the noise slider isn't used yet plot the imported or composed signal normally
                noisy_signal = self.ui.graph_1.listDataItems()[0].yData

            sampling_frequency = fmax_ratio_slider_value * self.max_freq
            updated_sample_points = int(round(sampling_frequency * self.signal_duration))
            self.ui.fs_number_label.setText(str(sampling_frequency) + 'Hz')
            self.ui.fmax_ratio_label.setText(str(fmax_ratio_slider_value) + 'x')

            # Clear the error plot in graph_3
            self.ui.graph_1.clear()
            self.ui.graph_2.clear()
            self.ui.graph_3.clear()
            self.update_plot(self.ui.graph_1, imported_signal['time'], noisy_signal, name=self.Signal.file_name)

            # Check if there are enough sample points to perform interpolation
            if updated_sample_points > 0:
                sampling_x_values = np.linspace(0, imported_signal['time'].max(), updated_sample_points)
                self.markers_x = sampling_x_values.tolist()
                self.markers_y = [noisy_signal[np.abs(imported_signal['time'] - x).idxmin()] for x in self.markers_x]
                marker = pg.ScatterPlotItem()
                marker.setData(x=self.markers_x, y=self.markers_y, size=3, pen=pg.mkPen(None), brush=(255, 0, 0))
                self.ui.graph_1.addItem(marker)

                num_samples = len(self.markers_x)
                t = np.linspace(0, num_samples * self.sampling_period, updated_sample_points)
                reconstructed_signal = np.zeros_like(t)

                for n in range(num_samples):
                    reconstructed_signal += self.markers_y[n] * np.sinc((t - n * self.sampling_period) / self.sampling_period)
                    
                self.update_plot(self.ui.graph_2, sampling_x_values, reconstructed_signal, name="Reconstructed Signal")

                # Create an interpolation function
                f = interp1d(sampling_x_values, reconstructed_signal, kind='cubic')
                # Interpolate to match the length of imported_signal['values']
                reconstructed_signal = f(imported_signal['time'])
                error_signal = noisy_signal - reconstructed_signal
                self.update_plot(self.ui.graph_3, imported_signal['time'], error_signal, name="Error Graph")

#Mixer Functions
    def compose_signal(self):
        self.use_composed_signal = False
        self.switch_function(self.use_composed_signal)
        # Clear the old signal data and plots
        self.ui.graph_1.clear()
        self.ui.graph_2.clear()
        self.ui.graph_3.clear()
        self.reset_slider()
        self.added_signal.amplitude = self.ui.amp_spinBox.value()
        self.added_signal.frequency = self.ui.freq_spinBox.value()
        self.added_signal.phase = self.ui.phase_spinBox.value()

        # Generate the sine wave data
        x = np.linspace(0, 10, 1000)  # Adjust the range and number of points as needed
        composed_signal = np.zeros(len(x))
        # Store the components of the new signal in a dictionary
        signal_components = {
            'amplitude': self.added_signal.amplitude,
            'frequency': self.added_signal.frequency,
            'phase': self.added_signal.phase
        }

        # Add the new signal to the dictionary of composed signals
        signal_number = len(self.added_signal.composed_signals) #Key number of 1st dict
        self.added_signal.composed_signals[signal_number] = signal_components #storing value

        # Iterate through each component and add it to the composed signal
        for component in self.added_signal.composed_signals.values():
            amplitude = component['amplitude']
            frequency = component['frequency']
            phase = component['phase']

            # Generate the sine wave for the current component
            component_signal = amplitude * np.sin(2 * np.pi * frequency * x + phase)

            # Add the component to the composed signal
            composed_signal += component_signal
        
        noisy_signal = composed_signal
        if self.ui.noise_slider.isSliderDown():
            noisy_signal = self.add_noise_to_signal(composed_signal, self.ui.noise_slider.value())
        # Update the PlotWidget with the new data
        self.ui.graph_1.plot(pen='w').setData(x, noisy_signal)
        print(self.added_signal.composed_signals)
        self.delete_signal_combobox()

    def calc_composed_parameters(self , max_freq):
        fmax_ratio_slider_value = self.ui.fmax_ratio_slider.value()
        self.max_freq_composed = max_freq
        self.sampling_frequency = fmax_ratio_slider_value * self.max_freq_composed
        self.sampling_period = 1 /self.sampling_frequency

    def delete_signal_combobox(self):
            # Clear the ComboBox first
            self.ui.delete_signal_combobox.clear()

            # Add keys from the composed_signal dictionary to the ComboBox
            for key in self.added_signal.composed_signals:
                self.ui.delete_signal_combobox.addItem(str(key))  

    def delete_selected_signal(self):
        selected_key = self.ui.delete_signal_combobox.currentText()
        if selected_key:
            selected_key = int(selected_key)
            # Check if the selected_key exists in the composed_signals dictionary
            if selected_key in self.added_signal.composed_signals:
                # Delete the selected signal
                del self.added_signal.composed_signals[selected_key]
                # Populate the ComboBox again to update the available keys
                self.delete_signal_combobox()

                # Clear the graph
                self.ui.graph_1.clear()
                self.ui.graph_2.clear()
                self.ui.graph_3.clear()

                # Calculate the mixture of the remaining signals
                composed_signal = np.zeros(1000)  # Assuming 1000 data points
                x = np.linspace(0, 10, 1000)
                for component in self.added_signal.composed_signals.values():
                    amplitude = component['amplitude']
                    frequency = component['frequency']
                    phase = component['phase']

                    # Generate the sine wave for the current component
                    component_signal = amplitude * np.sin(2 * np.pi * frequency * x + phase)

                    # Add the component to the composed signal
                    composed_signal += component_signal

                # Plot the new mixture signal
                self.ui.graph_1.plot(pen='w').setData(x, composed_signal)

    def save_composed_signals(self, filename):
        with open(filename, 'w') as json_file:
            json.dump(self.added_signal.composed_signals, json_file)

    def save_composed_signals_action(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(None, "Save Composed Signals", "", "JSON Files (*.json);;All Files (*)", options=options)

        if file_path:
            self.save_composed_signals(file_path)

    def load_composed_signals(self, filename):
        self.reset_slider()

        # Clear the graph
        self.ui.graph_1.clear()
        self.ui.graph_2.clear()
        self.ui.graph_3.clear()
        with open(filename, 'r') as json_file:
            loaded_signals = json.load(json_file)
            if loaded_signals:
                self.added_signal.composed_signals.update(loaded_signals)

            # Update the load_ex_combobox with the loaded file's name
            self.ui.load_ex_combobox.addItem(os.path.basename(filename))

            # Clear the graphs
            self.ui.graph_1.clear()
            self.ui.graph_2.clear()
            self.ui.graph_3.clear()

            if self.added_signal.composed_signals:
                # Calculate the mixture of the loaded signals
                x = np.linspace(0, 10, 1000)
                composed_signal = np.zeros(len(x))

                for component in self.added_signal.composed_signals.values():
                    amplitude = component['amplitude']
                    frequency = component['frequency']
                    phase = component['phase']

                    # Generate the sine wave for the current component
                    component_signal = amplitude * np.sin(2 * np.pi * frequency * x + phase)

                    # Add the component to the composed signal
                    composed_signal += component_signal

                self.ui.graph_1.plot(pen='w').setData(x, composed_signal)

            # Update the delete_signal_combobox with the keys of the dictionary
            self.delete_signal_combobox()

    def load_composed_signals_action(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(None, "Load Composed Signals", "", "JSON Files (*.json);;All Files (*)", options=options)

        if file_path:
            self.load_composed_signals(file_path)

    def sampled_composed_signal(self):
        self.use_composed_signal = False
        self.switch_function(self.use_composed_signal)
        fmax_ratio_slider_value = self.ui.fmax_ratio_slider.value()

        if self.added_signal.composed_signals:
            x = np.linspace(0, 10, 1000)  # Adjust the range and number of points as needed
            composed_signal = np.zeros(len(x))
            self.component_frequencies = []

            # Iterate through each component and add it to the composed signal
            for component in self.added_signal.composed_signals.values():
                amplitude = component['amplitude']
                frequency = component['frequency']
                phase = component['phase']

                self.component_frequencies.append(frequency)

                # Generate the sine wave for the current component
                component_signal = amplitude * np.sin(2 * np.pi * frequency * x + phase)

                # Add the component to the composed signal
                composed_signal += component_signal
                # Calculate the frequency of the mixed signal
                if self.component_frequencies:
                    self.mixed_frequency = sum(self.component_frequencies) / len(self.component_frequencies)
                else:
                    self.mixed_frequency = 0  # Handle the case where there are no components


            # Calculate parameters for the composed signal
            self.calc_composed_parameters(self.mixed_frequency)

            self.markers_x = []
            self.markers_y = []

            # Check if the noise_slider has changed
            if self.ui.noise_slider.isSliderDown():
                noisy_signal = self.add_noise_to_signal(composed_signal, self.ui.noise_slider.value())
                self.update_plot(self.ui.graph_1, x, noisy_signal, name="Composed Signal")
            else:
                # If noise_slider hasn't changed, use the signal displayed in graph_1
                noisy_signal = self.ui.graph_1.listDataItems()[0].yData

            sampling_frequency = fmax_ratio_slider_value * self.max_freq_composed
            updated_sample_points = int(sampling_frequency *10)
            self.ui.fs_number_label.setText(str(sampling_frequency) + 'Hz')
            self.ui.fmax_ratio_label.setText(str(fmax_ratio_slider_value) + 'x')

            # Clear the error plot in graph_3
            self.ui.graph_1.clear()
            self.ui.graph_2.clear()
            self.ui.graph_3.clear()

            # Update the PlotWidget with the new data
            self.ui.graph_1.plot(pen='w').setData(x, noisy_signal)
            

            # Check if there are enough sample points to perform interpolation
            if updated_sample_points > 0:
                sampling_x_values = np.linspace(0, 10, updated_sample_points)
                self.markers_x = sampling_x_values.tolist()
                self.markers_y = [noisy_signal[np.abs(x - t).argmin()] for t in sampling_x_values]
                marker = pg.ScatterPlotItem()
                marker.setData(x=self.markers_x, y=self.markers_y, size=3, pen=pg.mkPen(None), brush=(255, 0, 0))
                self.ui.graph_1.addItem(marker)
                # Assuming you already have the following variables
                num_samples = len(self.markers_x)
                t = np.linspace(0, num_samples * self.sampling_period, updated_sample_points)
                reconstructed_signal = np.zeros_like(t)

                # Create an interpolation function (e.g., cubic interpolation)
                f = interp1d(self.markers_x, self.markers_y, kind='cubic')

                # Interpolate the signal using the new time values (t)
                reconstructed_signal = f(t)

                self.update_plot(self.ui.graph_2, sampling_x_values, reconstructed_signal, name="Reconstructed Composed Signal")

                # Create an interpolation function
                f = interp1d(sampling_x_values, reconstructed_signal, kind='cubic')
                # Interpolate to match the length of x
                reconstructed_signal = f(x)
                error_signal = noisy_signal - reconstructed_signal
                self.update_plot(self.ui.graph_3, x, error_signal, name="Error Graph")