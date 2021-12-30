import requests, time, json, os, urllib, logging
from datetime import datetime
import pandas as pd
import numpy as np
try:
    f = open('settings.txt', "r")
    lastfmUsername = f.readline().rstrip("\n")
    startDateString = f.readline().rstrip("\n")
    dataFormat = f.readline()
    print("Settings file found\nUsername set as "+lastfmUsername+"\nStart date set as: "+startDateString+"\nData Format is: "+dataFormat)
except:
    lastfmUsername = str(input("Enter your username: "))
    startDateString = str(input("Please enter a start date in the following format YYYY.MM.DD: "))
    dataFormat = str(input("Please choose either artist, album, or track charts by typing your option as it is written: "))
detailedCheck = str(input("Would you like to grab images and tags for the top 30 "+dataFormat+"s of each week? Please respond Y or N: ")).lower()
detailedCheckBoolean = 'y' == detailedCheck
apiKey = "617512ecede614f849a5d87a44e8387a"#str(input("Enter your last.fm api key: "))
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
dataTable = pd.DataFrame()
arrayOfDateRanges = []
r = requests.get("http://ws.audioscrobbler.com/2.0/?method=user.getweeklychartlist&user="+lastfmUsername+"&api_key="+apiKey+"&format=json")
getweeklychartlistRAW = r.json()

#print(getweeklychartlistRAW)

pictureAndTagsMaster = {}

# endDateString = str(input("Please enter an end date in the following format YYYY.MM.DD"))
#fix the timezone, defaults to my current timezone
startDateUNIXtimestamp = time.mktime(datetime.strptime(startDateString, "%Y.%m.%d").timetuple())
# endDateUNIXtimestamp = time.mktime(datetime.strptime(endDateString, "%Y.%m.%d").timetuple())
def main():
    for x in getweeklychartlistRAW['weeklychartlist']['chart'] :
        if float(x['from']) >= float(startDateUNIXtimestamp) :
    #        print(x['from'], x['to'])
            arrayOfDateRanges.append([x['from'], x['to']])
    count = 1
    for y in arrayOfDateRanges :
        print("Working on Week "+str(count)+" out of "+str(len(arrayOfDateRanges)))
        weeklyDataDictionary = {}
        rTwo = requests.get("http://ws.audioscrobbler.com/2.0/?method=user.getweekly"+dataFormat+"chart&user="+lastfmUsername+"&from="+y[0]+"&to="+y[1]+"&api_key=617512ecede614f849a5d87a44e8387a&format=json")
        weeklyJSON = rTwo.json()
        weeklyRank = 1
        if detailedCheckBoolean:
            print("Getting pictures and tags for top 30 "+dataFormat+"s")
        for z in weeklyJSON['weekly'+dataFormat+'chart'][dataFormat] :
            # print("Working on "+dataFormat+" "+str(weeklyRank)+" out of "+str(len(weeklyJSON['weekly'+dataFormat+'chart'][dataFormat])))
            if dataFormat == "artist":
                name = str(z['name'])
            else:
                name = str(z['name'])+" ("+str(z['artist']['#text'])+")"
            playcount = int(z['playcount'])
            if detailedCheckBoolean:
                if weeklyRank < 31:
                    if name in pictureAndTagsMaster:
                        pictureAndTags = pictureAndTagsMaster[name]
                    else:
                        if dataFormat == "artist":
                            pictureAndTags = getArtistDetails(str(z['name']))
                        else:
                            pictureAndTags = getAlbumOrTrackDetails(str(z['name']), str(z['artist']['#text']))
                        try:
                            pictureAndTagsMaster[name] = {'url': pictureAndTags[0], 'First Tag': pictureAndTags[1][0], 'Tags': pictureAndTags[1]}
                        except IndexError:
                            pictureAndTagsMaster[name] = {'url': pictureAndTags[0], 'First Tag': '', 'Tags': ''}
            weeklyDataDictionary[name] = [playcount]
            # try:
            #     if weeklyRank < 31:
            #         weeklyDataDictionary[name] = [pictureAndTags[0], pictureAndTags[1][0], pictureAndTags[1] ,playcount]
            #     else:
            #         weeklyDataDictionary[name] = ["","",[],playcount]
            # except IndexError:
            #     print("Error with getting tags")
            #     print(name, pictureAndTags)
            #     try:
            #         weeklyDataDictionary[name] = [pictureAndTags[0],"",[],playcount]
            #     except:
            #         print("Error getting image url: ",name)
            #         weeklyDataDictionary[name] = ["","",[],playcount]
            weeklyRank += 1
        weeklyDataFrame = pd.DataFrame(data=weeklyDataDictionary)
        weeklyDataFrame = weeklyDataFrame.T
        fromReadableTimeStamp = datetime.utcfromtimestamp(int(y[0])).strftime('%Y.%m.%d')
        toReadableTimeStamp = datetime.utcfromtimestamp(int(y[1])).strftime('%Y.%m.%d')
        subtitle = str(fromReadableTimeStamp)+" - "+str(toReadableTimeStamp)
        weeklyDataFrame = weeklyDataFrame.rename(columns={0:"Week"+str(count)+" "+subtitle})
        # file_name = "Week"+str(count)+"_"+datetime.fromtimestamp(int(y[0])).strftime('%Y%m%d')+"-"+datetime.fromtimestamp(int(y[1])).strftime('%Y%m%d')
    #    weeklyDataFrame.to_csv(file_name+".csv")
    #    print(weeklyDataFrame)
        if count == 1 :
            dataTable = weeklyDataFrame
        else :
            dataTable = pd.concat([dataTable,weeklyDataFrame], axis=1, sort=False)
        count += 1
    #    print(dataTable)
    # print(dataTable)
    print("Finished gathering data, arranging data tables and creating timeframe options.")
    dataTable = dataTable.replace(r'^\s*$', 0, regex=True) # replace any blanks with 0
    dataTable = dataTable.fillna(0) # replace any nan with 0
    # print(pictureAndTagsMaster)
    # d = {k: v for k, v in pictureAndTagsMaster.items()}
    # detailsDataTable = pd.DataFrame.from_dict(data=d,orient='index')
    detailsDataTable = pd.DataFrame(data=pictureAndTagsMaster)
    detailsDataTable = detailsDataTable.T
    # detailsDataTable = pd.concat([detailsDataTable,dataTable], axis=1, sort=False)
    weeklyDataTable = dataTable
    monthlyDataTable = dataTable.groupby((np.arange(len(dataTable.columns)) // 4) + 1, axis=1).sum().add_prefix('Month')
    quarterlyDataTable = dataTable.groupby((np.arange(len(dataTable.columns)) // 13) + 1, axis=1).sum().add_prefix('Quarter')
    semsterlyDataTable = dataTable.groupby((np.arange(len(dataTable.columns)) // 26) + 1, axis=1).sum().add_prefix('Semester')
    yearlyDataTable = dataTable.groupby((np.arange(len(dataTable.columns)) // 52) + 1, axis=1).sum().add_prefix('Year')
    # Adding tags and images
    weeklyDataTable = pd.concat([detailsDataTable,weeklyDataTable], axis=1, sort=False)
    monthlyDataTable = pd.concat([detailsDataTable,monthlyDataTable], axis=1, sort=False)
    quarterlyDataTable = pd.concat([detailsDataTable,quarterlyDataTable], axis=1, sort=False)
    semsterlyDataTable = pd.concat([detailsDataTable,semsterlyDataTable], axis=1, sort=False)
    yearlyDataTable = pd.concat([detailsDataTable,yearlyDataTable], axis=1, sort=False)
    # monthlyDataTable = pd.DataFrame(np.add.reduceat(dataTable.values, np.arange(len(dataTable.columns))[::4], axis=1))
    # monthlyDataTable.columns = monthlyDataTable.columns + 1
    # monthlyDataTable.add_prefix('Month')
    weeklyDataTable.to_csv(os.path.join(__location__,"weeklyData.csv"))
    monthlyDataTable.to_csv(os.path.join(__location__,"monthlyData.csv"))
    quarterlyDataTable.to_csv(os.path.join(__location__,"quarterlyData.csv"))
    semsterlyDataTable.to_csv(os.path.join(__location__,"semesterData.csv"))
    yearlyDataTable.to_csv(os.path.join(__location__,"yearlyData.csv"))
    detailsDataTable.to_csv(os.path.join(__location__,"detailsDataTable.csv"))




def getAlbumOrTrackDetails(albumOrTrack, artist):
    encodedAlbumOrTrack = urllib.parse.quote(str(albumOrTrack).encode('utf-8'))
    encodedArtist = urllib.parse.quote(str(artist).encode('utf-8'))
    r = requests.get("http://ws.audioscrobbler.com/2.0/?method="+dataFormat+".getInfo&user="+lastfmUsername+"&api_key="+apiKey+"&"+dataFormat+"="+encodedAlbumOrTrack+"&artist="+encodedArtist+"&format=json")
    response = r.json()
    try:
        if response['error'] == '6': # No album or track found
            print("No "+dataFormat+" found for: "+albumOrTrack+" by "+artist)
            return["",[]]
    except:
        try:
            tags = []
            urlImage = ""
            if dataFormat == "track":
                try:
                    for image in response[dataFormat]['album']['image']:
                        if image['size'] == "large":
                            urlImage = image['#text']
                except KeyError:
                    logging.exception("No album found for track: "+albumOrTrack)
                    urlImage = ''
                for tag in response[dataFormat]['toptags']['tag']:
                    tags.append(tag['name'].title())
            else:
                for image in response[dataFormat]['image']:
                    if image['size'] == "large":
                        urlImage = image['#text']
                for tag in response[dataFormat]['tags']['tag']:
                    tags.append(tag['name'].title())
        except KeyError:
            logging.exception("Somehow, "+dataFormat+", "+albumOrTrack+", does not exist")
            urlImage = ''
            tags = []
        return [urlImage, tags]

def getArtistDetails(artist):
    encodedArtist = urllib.parse.quote(str(artist).encode('utf-8'))
    r = requests.get("http://ws.audioscrobbler.com/2.0/?method=artist.getInfo&user="+lastfmUsername+"&api_key="+apiKey+"&artist="+encodedArtist+"&format=json")
    response = r.json()
    tags = []
    urlImage = ""
    try:
        for image in response[dataFormat]['image']:
            if image['size'] == "large":
                urlImage = image['#text']
        for tag in response[dataFormat]['tags']['tag']:
            tags.append(tag['name'].title())
    except KeyError:
        logging.exception("Somehow, artist, "+artist+", does not exist")
        urlImage = ''
        tags = []
    return [urlImage, tags]

if __name__ == '__main__':
    logf = os.path.join(__location__,"main_logfile.out")
    logging.basicConfig(filename=logf, level=logging.DEBUG)

    logging.debug('-----BEGIN NEW LOG SECTION-----')
    try:
        main()
    except:
        logging.exception('Got exception on main')
        raise