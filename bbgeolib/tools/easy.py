import fnmatch
import os
import re
 
def findfiles(dir, pattern):
    result = []
    patternregex = fnmatch.translate(pattern)
    for root, dirs, files in os.walk(dir):
        for basename in files:
            filename = os.path.join(root, basename)
            if re.search(patternregex, filename, re.IGNORECASE):
                result.append(filename)

    return result