import math


class NonLinearInterpolator:
    def __init__(self):
        
        # map X(in) values to Y(out) values, add each range you want
        self.curve = []
        
    def NLinterp(self, value, curve=None):
        
        if curve == None:
            curve = self.curve
        
        for r in range(len(curve)):
            
            segment = curve[r]
            
            # if in X range...
            if value >= segment[0][0] and value < segment[0][1]: 
                # calculate the interpolation of the segment
                cvalue = self.interpolate( value, segment[0][0], segment[0][1], segment[1][0], segment[1][1] )
                return cvalue
        
        return value
            
    def interpolate(self, value, leftMin, leftMax, rightMin, rightMax):
        # Figure out how 'wide' each range is
        leftSpan = leftMax - leftMin
        rightSpan = rightMax - rightMin

        # Convert the left range into a 0-1 range (float)
        valueScaled = float(value - leftMin) / float(leftSpan)

        # Convert the 0-1 range into a value in the right range.
        return rightMin + (valueScaled * rightSpan)
    
    
if __name__ == "__main__":
    
    nli = NonLinearInterpolator()
    
    for i in range(0,256):
        print "%3.2f;%3.2f" % (i, nli.NLinterp(i))
        