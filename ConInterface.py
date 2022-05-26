import tkinter
from tkinter import *

from PIL import ImageTk, Image
from tkinter import messagebox
from tkinter.filedialog import asksaveasfilename
import numpy
import nidaqmx
import nidaqmx.system._collections.device_collection as device
from nidaqmx.constants import Edge
import matplotlib.pyplot as plt
with nidaqmx.Task() as readTask:

#TODO: Fix single channel (other todo)
    #Create tk root and properties
    root = Tk()
    root.title('Continuous Interface')
    root.iconbitmap('cbu-icon.ico')
    root.config(bg='light gray')

    #Assign font styles
    labelFont = ('Courier', 12)
    entryFont = ('Courier', 12, ('italic', 'bold'))
    btnFont = ('Courier', 12, 'bold')

    #CBU corner logo (bottom right)
    footerFrame = tkinter.Frame(root, bg='light gray')
    logo = ImageTk.PhotoImage(Image.open('Logo.jpg').resize((100, 37)))
    label = Label(footerFrame, image=logo, borderwidth=0)
    footerFrame.pack(side='bottom', fill='x', padx=5)
    label.pack(side='right', padx=5, pady=5)

    #Start boolean flag as False, list as empty
    check = False
    data = []

    def config():
        global numChan
        numChan = chanNumber.get()
        if checkEntry(numChan):
            #Convert string entry into integer
            numChan = int(numChan)

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

            readTask.timing.cfg_samp_clk_timing(rate=100, sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS)

            #Return true if all checks and set up pass
            return True

        #Return False if something does not pass
        return False


    '''
    Helper function for the configure function, checks to see whether
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
    Sets the boolean flag to True, allowing the record function to read in data.
    Also deactivates the start button, and activates the stop button.
    '''
    def start():
        if config():
            global check
            check = True
            stopBtn['state'] = NORMAL
            startBtn['state'] = DISABLED


    '''
    Continuously reads in a single sample from the desired number of channels at a frequency 
    of 100Hz. The samples are compiled into a single data set that is later exported to a .txt file.
    '''
    def record():
        # TODO: If only one channel, returns scalar, not list
        if check:
            sample = readTask.read()
            print(sample[:])
            data.append(sample)
        root.after(1, record)


    '''
    Ends the record recursion by setting the boolean flag to False, and automatically initiates the ending sequence
    for the program.
    '''
    def stop():
        #Set flag to False
        global check
        check = False

        #Stop task
        readTask.stop()

        #Convert compiled list to numpy array
        dataArray = numpy.array(data)

        #Call helper functions to plot and save
        plotChannels(dataArray)
        askSave(dataArray)

        #Quit the program
        root.destroy()

    '''
    Helper function which takes in the 2D matrix for the channel data. The function
    can support up to 6 channels, with any number dynamically resizing to take up the total figure space.
    '''
    def plotChannels(yAxisMatrix):
        #Set up time axis
        numSamp = len(yAxisMatrix)
        duration = numpy.arange(numSamp)
        timeArray = duration * 0.01

        #Set figure and color list for channels
        fig = plt.figure()
        colors = ['green', 'yellow', 'blue', 'red', 'black', 'orange']

        #Plot channels
        for position in range(0, numChan):
            plt.subplot(numChan, 1, position + 1)
            #Checks to see if EMG spiker shield channels are surpassed, color defaults to purple
            if position > 5:
                colorStr = 'purple'
            else:
                colorStr = colors[position]
            plt.plot(timeArray, yAxisMatrix[:, position], color=colorStr, label='C.' + str(position))
            plt.legend(loc='upper right', handlelength=0, handletextpad=0, fancybox=True)
            plt.grid()
            plt.yticks([2.5])

        #Set overall labels
        plt.subplots_adjust(hspace=.0)
        fig.supxlabel('Time (s)')
        fig.supylabel('Voltage (V)')
        plt.show()

        #Print final sample number to console to confirm correct time
        print('numSamp: ' + str(numSamp))



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


    #Channel Label
    chanLabel = Label(root, text='Number of Channels', bg='light gray', font=labelFont)
    chanLabel.pack(padx=5, pady=(10, 0))
    #Channel Entry
    chanNumber = Entry(root, borderwidth=3, bg='light blue', font=entryFont)
    chanNumber.pack(padx=10)

    #Start Button
    startBtn = Button(root, text='Start', command=start, font=btnFont)
    startBtn.pack(side='left', padx=(20, 0), pady=15)

    #Stop Button
    stopBtn = Button(root, text='Stop', command=stop, font=btnFont, fg='red', state=DISABLED, padx=6)
    stopBtn.pack(side='right', padx=(0, 20), pady=15)

    root.after(1, record)
    root.mainloop()
