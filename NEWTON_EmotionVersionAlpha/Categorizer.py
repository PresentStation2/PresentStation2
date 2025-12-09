def Categorize(features, duration):
    gender = features[1]

    meanF0 = float(features[0][0])
    F0std = float(features[0][1])
    meanF1 = float(features[0][2])
    H1minusA3 = float(features[0][3])
    pauseCount = float(features[0][4])

    categories = {
        "meanF0": 0,
        "F0std": 0,
        "meanF1": 0,
        "H1minusA3": 0,
        "pauseCount": 0
    }
    
    #Female values
    if gender == 'Female':

        match meanF0:
            case x if x < 150: categories["meanF0"] = 1
            case x if 150 <= x < 190: categories["meanF0"] = 2
            case x if 190 <= x < 210: categories["meanF0"] = 3
            case x if 210 <= x < 240: categories["meanF0"] = 4
            case x if x >= 240: categories["meanF0"] = 5

        match F0std:
            case x if x < 25: categories["F0std"] = 1
            case x if 25 <= x < 45: categories["F0std"] = 2
            case x if 45 <= x < 60: categories["F0std"] = 3
            case x if 60 <= x < 75: categories["F0std"] = 4
            case x if x >= 75: categories["F0std"] = 5

        match meanF1:
            case x if x < 350: categories["meanF1"] = 1
            case x if 350 <= x < 500: categories["meanF1"] = 2
            case x if 500 <= x <= 700: categories["meanF1"] = 3

        match H1minusA3:
            case x if x > -800: categories["H1minusA3"] = 1
            case x if -2000 < x <= -800: categories["H1minusA3"] = 2
            case x if -3000 < x <= -2000: categories["H1minusA3"] = 3
            case x if -4000 < x <= -3000: categories["H1minusA3"] = 4
            case x if x <= -4000: categories["H1minusA3"] = 5

        match pauseCount:
            case x if x > 26 * duration: categories["pauseCount"] = 5
            case x if 20 * duration < x <= 26 * duration: categories["pauseCount"] = 4
            case x if 14 * duration < x <= 20 * duration: categories["pauseCount"] = 3
            case x if 6 * duration < x <= 14 * duration: categories["pauseCount"] = 2
            case x if x <= 6 * duration: categories["pauseCount"] = 1



    #Male values
    elif gender == 'Male':

        match meanF0:
            case x if x < 100: categories["meanF0"] = 1
            case x if 100 <= x < 140: categories["meanF0"] = 2
            case x if 140 <= x < 170: categories["meanF0"] = 3
            case x if 170 <= x < 190: categories["meanF0"] = 4
            case x if x >= 190: categories["meanF0"] = 5

        match F0std:
            case x if x < 15: categories["F0std"] = 1
            case x if 15 <= x < 30: categories["F0std"] = 2
            case x if 30 <= x < 50: categories["F0std"] = 3
            case x if 50 <= x < 65: categories["F0std"] = 4
            case x if x >= 65: categories["F0std"] = 5

        match meanF1:
            case x if x < 320: categories["meanF1"] = 1
            case x if 320 <= x < 450: categories["meanF1"] = 2
            case x if 450 <= x <= 750: categories["meanF1"] = 3

        match H1minusA3:
            case x if x > -1000: categories["H1minusA3"] = 1
            case x if -2500 < x <= -1000: categories["H1minusA3"] = 2
            case x if -3500 < x <= -2500: categories["H1minusA3"] = 3
            case x if -5000 < x <= -3500: categories["H1minusA3"] = 4
            case x if x <= -5000: categories["H1minusA3"] = 5

        match pauseCount:
            case x if x > 26 * duration: categories["pauseCount"] = 5
            case x if 20 * duration < x <= 26 * duration: categories["pauseCount"] = 4
            case x if 14 * duration < x <= 20 * duration: categories["pauseCount"] = 3
            case x if 6 * duration < x <= 14 * duration: categories["pauseCount"] = 2
            case x if x <= 6 * duration: categories["pauseCount"] = 1

    #Unknown gender
    else:
        print("Cannot categorize")
        return None

    #Dictionary for priorities

    priorities = {
        "meanF0": 3,
        "F0std": 5,
        "meanF1": 2,
        "H1minusA3": 1,
        "pauseCount": 4
    }

    #Clustering the categories by type

    extreme_low = []
    extreme_high = []
    average = []
    good = []

    for key, value in categories.items():
        if value == 1:
            extreme_low.append(key)
        elif value == 2:
            average.append(key)
        elif value == 3:
            good.append(key)
        elif value == 4:
            average.append(key)
        elif value == 5:
            extreme_high.append(key)

    #Summing up by category types
    good_sum = 0
    average_sum = 0
    extreme_low_sum = 0
    extreme_high_sum = 0

    for i in good:
        good_sum += priorities[i]*1
    for i in average:
        average_sum += priorities[i]*2 
    for i in extreme_low:
        extreme_low_sum += priorities[i]*3
    for i in extreme_high:
        extreme_high_sum += priorities[i]*3

    #Determine body color by good, average or extreme
    extreme_sum = extreme_low_sum + extreme_high_sum

    color_indicator = ""

    if good_sum >= average_sum and good_sum >= extreme_sum:
        color_indicator = "good"
    elif average_sum >= good_sum and average_sum >= extreme_sum:
        color_indicator = "average"
    else:
        color_indicator = "extreme"

    #Determine face
    face_indicator = ""

    if color_indicator == "good":
        face_indicator = "good"
    elif color_indicator == "average":
        face_indicator = "average"
    elif color_indicator == "extreme":
        if extreme_high_sum >= extreme_low_sum:
            face_indicator = "extreme_high"
        else:
            face_indicator = "extreme_low"
        
    #Icons
    icon_indicator = ""
    highest = 0
    extreme = []

    extreme.extend(extreme_low)
    extreme.extend(extreme_high)

    for i in extreme:
        current_highest = priorities[i] * 3

        if current_highest > highest:
            highest = current_highest
            icon_indicator = i

    for i in average:
        current_highest = priorities[i] * 2

        if current_highest > highest:
            highest = current_highest
            icon_indicator = i

    print("Categories:", categories)
    print("Color indicator:", color_indicator)
    print("Face indicator:", face_indicator)
    print("Icon indicator:", icon_indicator)

    return categories, color_indicator, face_indicator, icon_indicator