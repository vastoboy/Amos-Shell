import os
import time
import win32gui
import win32ui
import win32con
from PIL import Image
from datetime import datetime


class GeneralFeatures:

    def __init__(self):
        self.now = datetime.now()


    def screenshot(self):
        # Set the width and height of the screenshot
        width = 1920
        height = 1080

        # Reference https://learn.microsoft.com/en-us/windows/win32/gdi/memory-device-contexts
        bmpfilename = "screenshot.bmp"
        pngfilename = "screenshot.png"

        hwnd = win32gui.FindWindow(None, " ")  # Find the window by its title
        wDC = win32gui.GetWindowDC(hwnd)  # Get the device context (DC) for the entire window
        dcObj = win32ui.CreateDCFromHandle(wDC)  # Create a device context (DC) from the window's DC
        cDC = dcObj.CreateCompatibleDC()  # Create a compatible DC for working with bitmaps
        dataBitMap = win32ui.CreateBitmap()  # Create a bitmap compatible with the specified DC
        dataBitMap.CreateCompatibleBitmap(dcObj, width, height)
        cDC.SelectObject(dataBitMap)  # Select the bitmap into the DC so that it can be drawn on
        cDC.BitBlt((0, 0), (width, height), dcObj, (0, 0),
                   win32con.SRCCOPY)  # Use BitBlt to copy the contents of the window's DC to the bitmap

        # Save the bitmap to a file
        dataBitMap.SaveBitmapFile(cDC, bmpfilename)

        # Convert BMP to PNG
        bmp_image = Image.open(bmpfilename)
        bmp_image.save(pngfilename, format='PNG')

        # Free Resources
        dcObj.DeleteDC()
        cDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, wDC)
        win32gui.DeleteObject(dataBitMap.GetHandle())

        # Remove the BMP file (optional, if you don't need it)
        os.remove(bmpfilename)





