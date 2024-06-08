import os
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D
import serial
import serial.tools.list_ports
import time
import seabreeze
seabreeze.use('pyseabreeze')
import seabreeze.spectrometers as sb
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

os.environ['PYUSB_BACKEND'] = 'libusb'

reference_intensities = np.array([])
reference_wavelengths = np.array([])
all_angles = []
all_transmittances = []
reference_file_path = ""

class SpectrometerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ABspectro")
        self.geometry("1200x800")

        self.spectrometer = None
        self.wavelength_min = 200
        self.wavelength_max = 850

        self.protocol("WM_DELETE_WINDOW", self.on_closing)  # Ensure program ends on window close

        self.create_widgets()
        self.disable_all_buttons()

    def on_closing(self):
        # Handle the window closing event
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.quit()
            self.destroy()

    def create_widgets(self):
        # Create control frame for buttons
        self.control_frame = tk.Frame(self)
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        # Create graph frame for plots
        self.graph_frame = tk.Frame(self)
        self.graph_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Create and add buttons
        self.spectrometer_button = tk.Button(self.control_frame, text="Choose spectrometer", command=self.choose_spectrometer)
        self.spectrometer_button.pack(pady=5)

        self.plot_ref_button = tk.Button(self.control_frame, text="Plot reference graph", command=self.plot_reference_and_realtime_measurement)
        self.plot_ref_button.pack(pady=5)

        self.save_ref_button = tk.Button(self.control_frame, text="Save reference datas", command=self.save_reference_spectrum)
        self.save_ref_button.pack(pady=5)

        self.plot_trans_button = tk.Button(self.control_frame, text="Plot transmittance graph", command=self.plot_transmittance_graph)
        self.plot_trans_button.pack(pady=5)

        self.save_trans_button = tk.Button(self.control_frame, text="Save transmittance datas", command=self.save_transmittance_spectrum_as_text)
        self.save_trans_button.pack(pady=5)

        self.start_motor_button = tk.Button(self.control_frame, text="Start motor (angle measurements)", command=self.start_motor_program)
        self.start_motor_button.pack(pady=5)

        self.plot_3d_button = tk.Button(self.control_frame, text="Plot 3D graph", command=self.plot_3d_graph)
        self.plot_3d_button.pack(pady=5)

        self.save_3d_button = tk.Button(self.control_frame, text="Save 3D datas", command=self.save_final_3d_data)
        self.save_3d_button.pack(pady=5)

        # Create and set up the plot area and the toolbar
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.graph_frame)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.ani = None

        # Create and set up the 3D plot area
        self.fig_3d = plt.figure()
        self.ax_3d = self.fig_3d.add_subplot(111, projection='3d')
        self.canvas_3d = FigureCanvasTkAgg(self.fig_3d, master=self.graph_frame)



    def disable_all_buttons(self):
        # Disable all buttons initially except Choose Spectrometer
        self.plot_ref_button.config(state=tk.DISABLED)
        self.save_ref_button.config(state=tk.DISABLED)
        self.plot_trans_button.config(state=tk.DISABLED)
        self.save_trans_button.config(state=tk.DISABLED)
        self.start_motor_button.config(state=tk.DISABLED)
        self.plot_3d_button.config(state=tk.DISABLED)
        self.save_3d_button.config(state=tk.DISABLED)

    def enable_buttons(self, buttons):
        # Enable specified buttons
        for button in buttons:
            button.config(state=tk.NORMAL)

    def disable_buttons(self, buttons):
        # Disable specified buttons
        for button in buttons:
            button.config(state=tk.DISABLED)

    def choose_spectrometer(self):
        # Automatically detect and choose the spectrometer
        devices = sb.list_devices()
        if len(devices) == 0:
            print("No spectrometer was found.")
            messagebox.showerror("Error", "No spectrometer detected.")
            return

        self.spectrometer = sb.Spectrometer(devices[0])  # Automatically choose the first available spectrometer
        model = devices[0].model

        if model == 'USB2000PLUS':
            self.wavelength_min = 200
            self.wavelength_max = 850
        elif model == 'SR2':
            self.wavelength_min = 649
            self.wavelength_max = 1300

        print(f"Spectrometer {self.spectrometer.model} selected.")
        messagebox.showinfo("Information", f"Spectrometer {self.spectrometer.model} selected.")
        self.enable_buttons([self.plot_ref_button])
        self.disable_buttons([self.spectrometer_button])
        
        

    def plot_reference_and_realtime_measurement(self):
        # Plot the reference graph and start real-time measurement
        messagebox.showinfo("Attention", "Adjust the light intensity.")
        if not self.spectrometer:
            self.choose_spectrometer()
        if not self.spectrometer:
            return

        self.ax.clear()
        self.line, = self.ax.plot([], [])
        self.ax.set_xlim(self.wavelength_min, self.wavelength_max)
        self.ax.set_ylim(0, 65535)
        self.ax.set_xlabel('Wavelength (nm)')
        self.ax.set_ylabel('Intensity')
        self.ax.set_title('Reference Measurement')

        self.ani = FuncAnimation(self.fig, self.update_plot, fargs=(self.line,), interval=500, cache_frame_data=False)
        self.canvas.draw()
        self.enable_buttons([self.save_ref_button])
        self.disable_buttons([self.plot_ref_button])

    def take_reference_measurement(self):
        # Take reference measurement from the spectrometer
        global reference_intensities, reference_wavelengths
        reference_intensities = self.spectrometer.intensities()
        reference_wavelengths = self.spectrometer.wavelengths()

    def update_plot(self, frame, line):
        # Update the plot in real-time
        if self.spectrometer:
            wavelengths = self.spectrometer.wavelengths()
            intensities = self.spectrometer.intensities()
            line.set_data(wavelengths, intensities)
            self.ax.relim()
            self.ax.autoscale_view()
            self.canvas.draw()
            return line,

    def save_reference_spectrum(self):
        # Save the reference spectrum data
        global reference_intensities, reference_wavelengths
        if not self.spectrometer:
            print("No spectrometer available.")
            return

        self.take_reference_measurement()  # Update reference data at the moment of saving
        if not len(reference_wavelengths) or not len(reference_intensities):
            print("No reference data to save.")
            return

        root = tk.Tk()
        root.withdraw()
        reference_file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")], title="Save Reference Data")
        if reference_file_path:
            try:
                with open(reference_file_path, 'w') as file:
                    file.write("Wavelength\tIntensity\n")
                    for wavelength, intensity in zip(reference_wavelengths, reference_intensities):
                        file.write(f"{wavelength}\t{intensity}\n")
                print(f"Reference data saved successfully at {reference_file_path}.")
                self.enable_buttons([self.plot_trans_button])
                self.disable_buttons([self.save_ref_button])
            except Exception as e:
                print(f"Failed to save reference data: {e}")

    def plot_transmittance_graph(self):
        # Plot the transmittance graph
        messagebox.showinfo("Attention", "Please insert the filter into the setup after pressing OK.")
        if not self.spectrometer:
            self.choose_spectrometer()
        if not self.spectrometer or reference_intensities.size == 0:
            print("Reference data is not saved yet.")
            return

        self.ax.clear()
        self.line, = self.ax.plot([], [])
        self.ax.set_xlim(self.wavelength_min, self.wavelength_max)
        self.ax.set_ylim(0, 1)
        self.ax.set_xlabel('Wavelength (nm)')
        self.ax.set_ylabel('Transmittance')
        self.ax.set_title('Transmittance Measurement')

        self.ani = FuncAnimation(self.fig, self.update_transmittance_plot, fargs=(self.line,), interval=500, cache_frame_data=False)
        self.canvas.draw()
        self.enable_buttons([self.save_trans_button, self.start_motor_button])
        self.disable_buttons([self.plot_trans_button])

    def update_transmittance_plot(self, frame, line):
        # Update the transmittance plot in real-time
        if self.spectrometer:
            wavelengths = self.spectrometer.wavelengths()
            intensities = self.spectrometer.intensities() / reference_intensities
            line.set_data(wavelengths, intensities)
            self.ax.relim()
            self.ax.autoscale_view()
            self.canvas.draw()
            return line,

    def save_transmittance_spectrum_as_text(self):
        # Save the transmittance spectrum data
        if not self.spectrometer:
            print("No spectrometer available.")
            return

        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if file_path:
            try:
                intensities = self.spectrometer.intensities() / reference_intensities
                with open(file_path, 'w') as file:
                    file.write("Wavelength\tTransmittance\n")
                    for wavelength, transmittance in zip(reference_wavelengths, intensities):
                        file.write(f"{wavelength}\t{transmittance}\n")
                print(f"Transmittance data saved successfully at {file_path}.")
            except Exception as e:
                print(f"Failed to save transmittance data: {e}")

    def start_motor_program(self):
        # Start the motor program and save data at each step
        lancer_programme_moteur(self.spectrometer)
        self.enable_buttons([self.plot_3d_button])
        self.disable_buttons([self.start_motor_button])

    def plot_3d_graph(self):
        # Plot the 3D graph of transmittance vs wavelength and angle
        if not len(reference_wavelengths) or not len(all_angles) or not len(all_transmittances):
            print("No data to plot.")
            return
        self.ax_3d.clear()
        self.canvas.get_tk_widget().pack_forget()  # Hide the 2D plot
        self.canvas_3d.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        for i, angle in enumerate(all_angles):
            self.ax_3d.plot(reference_wavelengths, [angle]*len(reference_wavelengths), all_transmittances[i])
        self.ax_3d.set_xlim(self.wavelength_min, self.wavelength_max)
        self.ax_3d.set_zlim(0, 1)
        self.ax_3d.set_xlabel('Wavelength (nm)')
        self.ax_3d.set_ylabel('Angle (degrees)')
        self.ax_3d.set_zlabel('Transmittance')
        self.ax_3d.set_title('Transmittance Spectrum as a Function of Wavelength and Angle')

        self.canvas_3d.draw()
        self.enable_buttons([self.save_3d_button])
        self.disable_buttons([self.plot_3d_button])

    def save_final_3d_data(self):
        # Save the final 3D data
        if not len(reference_wavelengths) or not len(all_angles) or not len(all_transmittances):
            print("No data to save.")
            return
        root = tk.Tk()
        root.withdraw()
        final_3d_file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")], title="Save Final 3D Data")
        if final_3d_file_path:
            try:
                with open(final_3d_file_path, 'w') as file:
                    file.write("Wavelength\tAngle\tTransmittance\n")
                    for i, angle in enumerate(all_angles):
                        for wavelength, transmittance in zip(reference_wavelengths, all_transmittances[i]):
                            file.write(f"{wavelength}\t{angle}\t{transmittance}\n")
                print(f"Final 3D datas saved successfully at {final_3d_file_path}.")
            except Exception as e:
                print(f"Failed to save final 3D data: {e}")

def lancer_programme_moteur(spectrometer):
    # Function to run the motor program and save data at each angle
    global all_angles, all_transmittances, reference_intensities

    print("Starting motor program...")
    root = tk.Tk()
    root.withdraw()
    titre_fichier = simpledialog.askstring("File Title", "Enter the base title for data files:")

    if not titre_fichier:
        print("File title not provided.")
        return

    dossier_destination = filedialog.askdirectory()
    if not dossier_destination:
        print("No folder selected.")
        return

    # Automatically find the Arduino port
    arduino_ports = [p.device for p in serial.tools.list_ports.comports() if 'Arduino' in p.description]
    if not arduino_ports:
        print("No Arduino was found.")
        messagebox.showerror("Error", "No Arduino detected.")
        return
    port = arduino_ports[0]
    
    try:
        ser = serial.Serial(port, 9600)
    except serial.SerialException as e:
        print(f"Serial port connection error: {e}")
        return

    def envoyer_commande(direction):
        ser.write(direction.encode())
        print(f"Command sent: {direction}")

    time.sleep(2)

    # Save initial position data (0 degree) before moving the motor
    save_data(0, spectrometer, titre_fichier, dossier_destination)

    angles = [i * 3 for i in range(1, 16)] + [-i * 3 for i in range(1, 16)]  # Correct angle order
    compteur_fichier = 0  # Start at 0 to properly index angles list

    envoyer_commande('S')  # Start the motor after the initial measurement

    motor_finished = False
    while True:
        try:
            message = ser.readline().strip().decode()
        except serial.SerialException as e:
            print(f"Serial port read error: {e}")
            break

        if message:
            print("Arduino Message:", message)
        if message == 'B' and not motor_finished:
            motor_finished = True
            break

        if message.startswith('Step'):
            angle = angles[compteur_fichier]
            save_data(angle, spectrometer, titre_fichier, dossier_destination)
            compteur_fichier += 1

    ser.close()
    spectrometer.close()
    print("Information")
    messagebox.showinfo("Information", "Motor program has finished recording data.")

def save_data(angle, spectrometer, titre_fichier, dossier_destination):
    # Save data for each angle step
    global reference_intensities
    wavelengths = spectrometer.wavelengths()
    intensities = spectrometer.intensities()
    transmittances = intensities / reference_intensities

    all_angles.append(angle)
    all_transmittances.append(transmittances)

    nom_fichier = f"{titre_fichier}_{angle}deg.txt"
    chemin_fichier = os.path.join(dossier_destination, nom_fichier)

    try:
        with open(chemin_fichier, 'w') as file:
            file.write(f"Angle: {angle} degrees\n")
            for wavelength, transmittance in zip(wavelengths, transmittances):
                file.write(f"{wavelength}\t{transmittance}\n")
        print(f"Data saved in {chemin_fichier}")
    except Exception as e:
        print(f"Failed to save data in {chemin_fichier}: {e}")

if __name__ == "__main__":
    app = SpectrometerApp()
    app.mainloop()