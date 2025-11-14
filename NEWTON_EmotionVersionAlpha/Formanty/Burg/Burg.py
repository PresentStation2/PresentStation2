import numpy
from numpy.linalg import eig

class Polynomial():
    def __init__(self, coeffs):
        lenCoeffs = len(coeffs)
        self.lenCoeffs = lenCoeffs
        self.coefficients = numpy.zeros(lenCoeffs+1)
        
        for i in range(lenCoeffs):
            self.coefficients[i] = - coeffs[lenCoeffs - i -1]
        self.coefficients[-1] = 1.0
    
class Formant():
    def __init__(self, frequency, bandwidth):
        self.frequency = frequency
        self.bandwidth = bandwidth
        

class Burg():
    def __init__(self, nyquistFrequency, safetyMargin):
        self.nyquistFrequency = nyquistFrequency
        self.safetyMarginLower = safetyMargin
        self.safetyMarginUpper = nyquistFrequency - safetyMargin
        self.maxIterations = 80
    
    def computeBurg(self, audioData, poleCount):
        formants, coeffs = [], self.VECburg(audioData, poleCount)
        
        polynomial = Polynomial(coeffs)
        
        roots = self.Poly2Roots(polynomial)
        
        roots = self.Roots_fixIntoUnitCircle(roots)
    
        safeLow, safeUp, nyqByPi = self.safetyMarginLower, self.safetyMarginUpper, self.nyquistFrequency / numpy.pi
        
        for root in roots:
            if root.imag >= 0.0:
                f = numpy.abs( numpy.arctan2(root.imag, root.real) ) * nyqByPi
                if safeLow <= f <= safeUp:
                    bw = -numpy.log(self.CNorm(root)) * nyqByPi
                    formants.append(Formant(f,bw))
        
        formants.sort(key=lambda x: x.frequency)
                    
        return formants

    def CNorm(self,num):
        return num.real*num.real + num.imag*num.imag       
    
    def Poly2Roots(self, polynomial):
        coeffs = polynomial.coefficients
        n = polynomial.lenCoeffs
        
        # UpperHessenberg matrix
        upperHess = numpy.zeros((n,n))
                
        upperHess[0,-1] = - ( coeffs[0] / coeffs[-1] )
        for irow in range(1, n):
            upperHess[irow,-1] = - coeffs[irow] / coeffs[-1]
            upperHess[irow, irow-1] = 1.0

        vals = eig(upperHess)[0]
        
        #====================== without polishing ========================
        # return None if vals.shape[0] == 0 else vals
        #=================================================================
        return None if vals.shape[0] == 0 else self.Roots_Polynomial_polish(roots=vals, coeffs=coeffs)
    
    def Roots_Polynomial_polish(self,roots, coeffs):
        # complex roots are supposed to be in pairs
        i, newVals = 0, numpy.copy(roots)        
        while i < roots.shape[0]:
            root = roots[i]
            
            if root.imag != 0.0:
                polished = self.Polynomial_polish_complexroot_nr(root, coeffs)
                newVals[i] = polished 
                newVals[i+1] = polished.real - 1j*polished.imag
                i += 1            
            else:
                newVals[i] = self.Polynomial_polish_realroot_nr(root, coeffs)
            
            i += 1
        
        return newVals

    def Polynomial_polish_complexroot_nr(self, root, coeffs):

        zbest = numpy.copy(root)
        ymin = 100000000000000000000000000000000000000000000000000000000.0
        eps  = 0.000000000000000000000000000000000000000000000000000000001
        
        for iiter in range(self.maxIterations):
            y, dy = self.Polynomial_evaluateWithDerivative_z(coeffs, root);
            fabsy = numpy.abs(y)

            # We stop, because the approximation is getting worse.
            # Return the previous (hitherto best) value for z.    
            if fabsy > ymin or numpy.abs(fabsy-ymin) < eps:
                root = zbest
                return zbest

            ymin, zbest = fabsy, root
            if numpy.abs(dy) == 0.0:
                return zbest

            root -= y/dy
        del(iiter)
        return root

    def Polynomial_polish_realroot_nr(self, root, coeffs):
        
        xbest = numpy.copy(root)
        ymin = 100000000000000000000000000000000.0
        eps = 0.0000000000000000000000000000000001   
        
        for iiter in range(self.maxIterations):
            y, dy = self.Polynomial_evaluateWithDerivative_z(coeffs, root);
            fabsy = numpy.abs(y)

            if fabsy > ymin or numpy.abs(fabsy-ymin) < eps:
                root = xbest
                return xbest
            
            ymin, xbest = fabsy, root
            if numpy.abs(dy) == 0.0:
                return root
            
            root -= y/dy

        del(iiter)
        return root

    def Polynomial_evaluateWithDerivative_z(self, coeffs, root):
        pr, pi = coeffs[-1], 0.0
        dpr, dpi, x, y  = 0.0, 0.0, root.real, root.imag
        
        for i in range(len(coeffs)-2, -1, -1):
            tr = dpr;
            dpr = dpr * x - dpi * y + pr
            dpi =  tr * y + dpi * x + pi
            tr = pr
            pr =  pr * x - pi * y + coeffs[i]
            pi = tr * y +   pi * x

        val, delta = pr + 1j*pi, dpr + 1j*dpi

        return val, delta






    
    def Roots_fixIntoUnitCircle(self, roots):
        z10 = numpy.complex(1,0)
        for iroot in range(roots.shape[0]):
            if numpy.abs(roots[iroot]) > 1.0:
                roots[iroot] = z10 / numpy.conj(roots[iroot])

        return roots

    def VECBurg_XX(self, x, m):
        x = numpy.insert(x, 0, 0)
        m += 1
        n = x.shape[0]
        
        a = numpy.zeros(m)
      
        b1, b2, aa = numpy.zeros(n), numpy.zeros(n), numpy.zeros(m)
    
        b1 [1] = x [1]
        b2 [n - 2] = x [n-1]
        
        for j in range(2, n):
            b1[j] = x[j]
            b2[j-1] = x[j]
            
        for i in range(1, m):
            num, denum = 0.0, 0.0
            
            for j in range(1, n-i+1):
                num += b1[j] * b2[j]
                denum += b1 [j] * b1 [j] + b2 [j] * b2 [j]
    
            a [i] = 2.0 * num / denum
    
            for j in range(1, i):
                a [j] = aa [j] - a [i] * aa [i - j]
                
            if i < m:
                for j in range(1, i+1):
                    aa[j] = a[j]
                
                for j in range(1, n-i):
                    b1 [j] -= aa [i] * b2 [j]
                    b2 [j] = b2 [j + 1] - aa [i] * b1 [j + 1]                    
        return a

    
    def VECburg(self, x, m):
        n = x.shape[0]
        a, aa = list(numpy.zeros(m)), list(numpy.zeros(m))
        
        if n <= 2:
            a[0] = -1.0
            return 0.5 * (x[0] * x[0] + x[1] * x[1]) if n == 2 else x[0] * x[0]

        b1 = numpy.copy(x)
        b1[-1] = 0.0

        b2 = numpy.copy(x)
        b2[0] = 0.0
        b2 = numpy.roll(b2,-1)
        
        b1new, b2new = numpy.zeros(n), numpy.zeros(n)

        for i in range(m):
            num = numpy.dot(b1,b2)
            denum = numpy.dot(b1,b1)+numpy.dot(b2,b2)
            a[i] = 2.0 * num / denum
 
            for j in range(i):
                a[j] = aa[j] - a[i] * aa[i - j - 1]
                
            if (i < m-1):
                for j in range(i+1):
                    aa[j] = a[j]                          
                            
                aai = aa[i]
                b1new = b1-aai*b2
                b2new = b2-aai*b1
                b2new = numpy.roll(b2new,-1)
                 
                for j in range(n-i-2, n):
                    b1new[j] = 0.0
                    b2new[j] = 0.0
                 
                b1 = b1new
                b2 = b2new

        return a
    
    