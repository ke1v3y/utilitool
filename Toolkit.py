# Standard Libraries
import csv
import datetime
from time import time as ttime
from os import path, system, name as osname
from collections import Counter, MutableMapping
from functools import reduce


class ProgressCounter:
    """Progress counter object. Declare once per task and delete when done.
    
    Class variables:
    total -- integer representing maximum progress
    current -- integer value of current progress
    isRunning -- boolean representation of whether or not progress is being reported
    lastReported -- integer timestamp of last reported time
    reportInterval -- integer frequency in seconds to report progress
    size -- integer character width of progress bar
    """
    total = 0
    current = 0
    isRunning = False
    lastReported = 0
    reportInterval = 5
    size = 60

    def updateLastReported(self):
        """Return null. Updates the time last reported to the current time and checks if it is necessary to report."""
        now = int(ttime())
        if now - self.lastReported > self.reportInterval:
            self.report()
            self.lastReported = now
        return

    def handlePercentage(self):
        """Return string. Builds progress bar using defined class properties."""
        try:
            current = int((self.current / self.total) * self.size)
        except ZeroDivisionError:
            current = self.size
        filler = self.size - current
        output = ''
        for i in range(0, current):
            output += '='
        for j in range(0, filler):
            output += '-'
        return output

    def setTotal(self, total):
        """Return boolean. Sets the maximum progress value for a task.
        
        Argument keywords:
        total -- integer desired maximum progress value to set
        """
        self.total = total
        return True

    def updated(self):
        """Return boolean. Updates current progress count and checks to see if it
        is complete or needs to be reported.
        """
        self.current += 1
        if self.current == self.total:
            self.stop()
            self.report()
            return True
        self.updateLastReported()
        return False

    def report(self):
        """Return null. Prints current progress bar."""
        print('\n|' + self.handlePercentage() + '|')
        return

    def start(self):
        """Return boolean. Starts progress reporting."""
        self.isRunning = True
        self.updateLastReported()
        return True

    def stop(self):
        """Return boolean. Stops progress reporting."""
        self.isRunning = False
        return True


def updateInPlace(a, b):
    """Return updated object. Simple function for updating a value in place.
    
    Keyword arguments:
    a -- object to update
    b -- object to merge in
    """
    a.update(b)
    return a


def identifyDelimiter(infile):
    """Return string. Identifies the type of delimiter used in a text or CSV file.
    
    Keyword arguments:
    infile -- filename of file to process
    """
    maxLines = 10
    extension = str(infile)[str(infile).rfind('.') + 1:]
    if extension == 'xml':
        return 'xml'
    elif extension == 'json':
        return 'json'
    else:
        baseFileLength = len(path.join(scriptPath, '_Working'))
        if infile[baseFileLength + 3:baseFileLength + 4] == '.':
            return False
        delimiters = {
            '|': 0, ',': 0, '\t': 0, ':': 0, ';': 0, '~': 0, ' ': 0, '{': 0
                    }
        for d in delimiters:
            thisRowLength = 0
            try:
                activeFile = open(infile, 'r')
                currLine = 0
                for row in activeFile:
                    currLine += 1
                    if currLine < maxLines:
                        fields = row.split(d)
                        if thisRowLength != 0:
                            if thisRowLength == len(fields):
                                delimiters[d[0]] = len(fields) - 1
                            else:
                                delimiters[d[0]] = 0
                        else:
                            thisRowLength = len(fields)
                activeFile.close()
            except UnicodeDecodeError:
                with open(infile, 'rb') as f:
                    reader = csv.reader(f)
                    try:
                        for row in reader:
                            fields = row.split(d)
                            if thisRowLength != 0:
                                if thisRowLength == len(fields):
                                    delimiters[d[0]] = len(fields) - 1
                                else:
                                    delimiters[d[0]] = 0
                            else:
                                thisRowLength = len(fields)
                    except csv.Error:
                        return False
        delimiters2 = {k: v for k, v in delimiters.items() if v > 1}
        occurrences = []
        if len(delimiters2) > 1:
            intOcc = {}
            for d in delimiters2:
                x = 0
                y = 0
                for d2 in delimiters2:
                    activeFile = open(infile, 'r')
                    for row in activeFile:
                        fields = row.split(d)
                        for field in fields:
                            z = field.count(d2)
                            if z > 2:
                                z = 5
                            elif z > 0:
                                z = 1
                            else:
                                z = 0
                            y += z
                            x += 1
                    activeFile.close()
                    try:
                        avgOcc = y / x
                    except ZeroDivisionError:
                        avgOcc = 0
                    intOcc.update({d2: avgOcc})
                intOcc = {k: v for k, v in intOcc.items() if v > 0}
                occurrences.append(intOcc)
            keyTotals = (reduce(updateInPlace, (Counter(dict(x)) for x in occurrences)))
            delTotals = {}
            for d in delimiters2:
                thisKey = [k[d] for k in occurrences if k.get(d)]
                keyCount = len(thisKey)
                avgValue = keyTotals[d] / keyCount
                totalVariance = 0
                for k in thisKey:
                    totalVariance += abs(avgValue - k)
                delTotals[d] = totalVariance
            newDel = min(delTotals, key=delTotals.get)
        else:
            newDel = max(delimiters, key=delimiters.get)
        if newDel == '{':
            return 'json'
        return newDel


def flatten(val, parent='', sep='.'):
    """Return dictionary. Takes a set of nested dictionaries, lists, etc., 
    and flattens the data into a single dictionary. Calls itself internally
    to reach values that can be represented as a string.
    
    Keyword arguments:
    val -- nested dictionary/list object to flatten
    parent -- string dictionary key of parent element
    sep -- string separator used to split levels of data
    """
    items = []
    try:
        for k, v in val.items():
            newKey = '{0}{1}{2}'.format(parent, sep, k) if parent else k
            if isinstance(v, MutableMapping):
                newVal = flatten(v, newKey, sep)
                items.extend(newVal.items())
            elif isinstance(v, list):
                for subVal in v:
                    newVal = flatten(subVal, newKey, sep)
                    items.extend(newVal.items())
            else:
                items.append((newKey, v))
    except AttributeError:
        if parent == '':
            return val
        else:
            return {parent: val}
    return dict(items)


def dataToBit(val, invert):
    """Return string representation of bit value. Converts common text values
    to their bit equivalents, inverting them as required by the feed.
    
    Keyword arguments:
    val -- string value to convert
    invert -- boolean check for whether to invert truthiness of value
    """
    val = str(val).strip().upper()
    midVal = 0
    if val == 'YES':
        midVal = 1
    elif val == 'TRUE':
        midVal = 1
    elif val == '1':
        midVal = 1
    if invert:
        if midVal == 1:
            finVal = str(0)
        else:
            finVal = str(1)
    else:
        finVal = str(midVal)
    return finVal


def timestamp():
    """Return formatted timestamp as string."""
    return str(int(ttime()))


def datestamp():
    """Return formatted datestamp as string."""
    return str(datetime.datetime.fromtimestamp(int(ttime())).strftime('%Y%m%d%H%M'))


def dateString(modified):
    """Return formatted datestamp as string."""
    return str(datetime.datetime.fromtimestamp(modified).strftime('%Y-%m-%d %H:%M:%S'))


def wrap(raw, cutoff):
    """Return string. Soft wraps a string of text to a specified width.

    Keyword arguments:
    raw -- input string
    cutoff -- integer maximum width in characters
    """
    working = ''
    outTxt = []
    if len(raw) < cutoff:
        outTxt.append(raw)
    else:
        for i in raw.split():
            if len(working) + len(i) < cutoff:
                working += i + ' '
            else:
                outTxt.append(working.rstrip())
                working = i + ' '
        outTxt.append(working.rstrip())
    results = '\n'.join(outTxt)
    return results


def clearConsole():
    system('cls' if osname == 'nt' else 'clear')


# Global Variables
scriptPath = path.dirname(path.realpath(__file__))
