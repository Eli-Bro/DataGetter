import tkinter
from tkinter import *
from PIL import ImageTk, Image
from tkinter import messagebox
from tkinter.filedialog import asksaveasfilename
import numpy
import nidaqmx
import nidaqmx.system._collections.device_collection as device
from nidaqmx.constants import Edge
from nidaqmx.stream_readers import AnalogMultiChannelReader
import matplotlib.pyplot as plt

'''
Author(s): Created by Elijah Brown under the supervision of Dr. Kim
Date: May, 2022
Summary: The following program allows the user to set certain parameters in conjunction with
a National Instruments DAQ to read and save multiple EMG signals at once, saving them in a .txt file
with each active channel having its own column.
'''

#Create tk root and properties
root = Tk()
root.title('EMG Interface')
root.iconbitmap('cbu-icon.ico')
root.config(bg='light gray')

#Assign font styles
frameFont = ('Courier', 15, 'bold')
labelFont = ('Courier', 12)
entryFont = ('Courier', 12, ('italic', 'bold'))
btnFont = ('Courier', 12, 'bold')

#CBU corner logo (bottom right)
footerFrame = tkinter.Frame(root, bg='light gray')
logo = ImageTk.PhotoImage(Image.open('Logo.jpg').resize((100, 37)))
label = Label(footerFrame, image=logo, borderwidth=0)
footerFrame.pack(side='bottom', fill='x', padx=5)
label.pack(side='right', padx=5, pady=5)


'''
Command function for exit button, asks user a conformation before executing quit
'''
def exitConfirm():
    response = messagebox.askyesno("Exit Confirmation", "Exit the program?")
    if response:
        root.destroy()


#Exit button
exitBtn = Button(footerFrame, text='Exit', command=exitConfirm, font=btnFont, fg='red')
exitBtn.pack(side='left', padx=5, pady=5)


#Information Frame
frame = LabelFrame(root, text='Acquisition Parameters', bg='light gray',
                   borderwidth=3, font=frameFont, padx=5, pady=5)
frame.pack(padx=10, pady=5)


#Channel label
chanLabel = Label(frame, text='Number of Channels', bg='light gray', font=labelFont)
chanLabel.pack(anchor='w', padx=30)
#Channel Entry
chanNumber = Entry(frame, borderwidth=3, bg='light blue', font=entryFont)
chanNumber.pack(pady=(0, 10))


#Number label
numLabel = Label(frame, text='Number of Samples', bg='light gray', font=labelFont)
numLabel.pack(anchor='w', padx=30)
#Number entry
sampNumber = Entry(frame, borderwidth=3, bg='light blue', font=entryFont)
sampNumber.pack(pady=(0, 10))


#Frequency label
fqLabel = Label(frame, text='Sample Frequency (Hz)', bg='light gray', font=labelFont)
fqLabel.pack(anchor='w', padx=30)
#Frequency entry
frequency = Entry(frame, borderwidth=3, bg='light blue', font=entryFont)
frequency.pack(pady=(0, 10))


'''
Command function for the record button, which carries out a session sequence 
consisting the following components:
    1. Record from the specified number of channels over the given number of
    samples and frequency
    2. Graph the data for the user to visualize the result
    3. Give the user the option to save the .txt for the data
'''
def recordSession():
    #Gain current provided information (uses str to accept anything)
    numChan = chanNumber.get()
    numSamp = sampNumber.get()
    sampFreq = frequency.get()

    #Once all parameters are valid, begin recording
    if checkEntry(numChan) and checkEntry(numSamp) and checkEntry(sampFreq):
        with nidaqmx.Task() as readTask:
            #Set up device and channels, check for errors
            try:
                devNameList = device.DeviceCollection.device_names.__get__(0)
                devName = devNameList[0]
                readTask.ai_channels.add_ai_voltage_chan(devName + '/ai0:'
                                                         + str(int(numChan) - 1),
                                                         terminal_config=nidaqmx.constants.TerminalConfiguration.RSE)
            #Channel number exceeds device range
            except nidaqmx.errors.DaqError:
                messagebox.showerror('DAQ Error', 'Ensure channel number is within device range.')
                raise
            #DAQ is not recognized by system (i.e. not plugged in)
            except IndexError:
                messagebox.showerror('DAQ Error', 'System cannot find DAQ, ensure device is plugged in')
                raise

            #Record session after successful checks
            #Set up sampling frequency, number of samples
            readTask.timing.cfg_samp_clk_timing(rate=int(sampFreq), samps_per_chan=int(numSamp))

            #Create instance of reader
            reader = AnalogMultiChannelReader(readTask.in_stream)

            #Start reading
            readTask.start()

            #Allocate numpy array based on number of channels and samples
            valuesRead = numpy.zeros((int(numChan), int(numSamp)), dtype=numpy.float64)

            #Read analog data, update given array
            reader.read_many_sample(valuesRead, number_of_samples_per_channel=int(numSamp))
            readTask.stop()

            #Transpose array so that channels are columns
            valuesRead = numpy.transpose(valuesRead)

            #Set up time, x-axis
            duration = float(numSamp) / int(sampFreq)
            timeArray = numpy.linspace(0, duration, int(numSamp))

            #Call plotting function
            plotChannels(int(numChan), timeArray, valuesRead)

            #Ask user for save confirmation (plot still active)
            askSave(valuesRead)


'''
Helper function for the recordSession function, checks to see whether
the provided entry variable is non-empty and of type int
'''
def checkEntry(entry):
    strEntry = str(entry)

    if len(strEntry) == 0:
        messagebox.showerror('Invalid Parameters', 'Please ensure all parameters are filled out.')
        return False

    if not strEntry.isdigit() or int(strEntry) == 0:
        messagebox.showerror('Invalid Parameters', 'Please ensure all parameters are positive '
                                                   'integers with no non-numeric characters.\n' +
                             'Incorrect Parameter: ' + strEntry)
        return False

    return True


'''
Helper function which takes in the necessary information to plot channel output, such as
the number of channels, time for the x-axis, and 2D matrix for the channel data. The function
can support up to 6 channels, with any number dynamically resizing to take up the total 
figure space.
'''
def plotChannels(numChan, xAxis, yAxisMatrix):
    #Set figure and color list for channels
    fig = plt.figure()
    colors = ['green', 'yellow', 'blue', 'red', 'black', 'orange', 'purple', 'purple']

    #Plot channels
    for position in range(0, numChan):
        plt.subplot(numChan, 1, position+1)
        #Checks to see if EMG spiker shield channels are surpassed, color defaults to purple
        if position > 5:
            colorStr = 'purple'
        else:
            colorStr = colors[position]
        plt.plot(xAxis, yAxisMatrix[:, position], color=colorStr, label='C.' + str(position))
        plt.legend(loc='upper right', handlelength=0, handletextpad=0, fancybox=True)
        plt.grid()
        plt.margins(y=0.3)
        plt.yticks([round(numpy.min(yAxisMatrix[:, position], axis=0), 2),
                    round(numpy.max(yAxisMatrix[:, position], axis=0), 2)])

    #Set overall labels
    plt.subplots_adjust(hspace=.0)
    fig.supxlabel('Time (s)')
    fig.supylabel('Voltage (V)')
    plt.show()


'''
Helper function that asks the user for a file name and path via the file dialog,
saving the generated .txt file from the recorded session
'''
def askSave(data):
    response = messagebox.askyesno('File Save Confirmation', 'Would you like to save the .txt file?\n ' +
                                                             'The data corresponds to the plot shown.')
    #User wants to save file
    if response:
        #Set up dialog
        file = asksaveasfilename(defaultextension='.txt',
                                 filetypes=[('All Files', '*.*'), ('Text Documents', '*.txt')])

        #Handle exception if user exits file dialog
        if file is None:
            return
        
        #Save text file to specified file
        numpy.savetxt(file, data, fmt='%.2e')

    else:
        plt.close('all')


#Record Button
recordBtn = Button(root, text='Record', command=recordSession, font=btnFont)
recordBtn.pack(pady=15)

root.mainloop()
