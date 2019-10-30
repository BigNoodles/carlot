Script written by Damian Hamilton 
Send questions to: damianhamilton25@hotmail.com
October 14, 2019

This script takes a CSV file containing the make, model, and expected total
number of cars, and scrapes the advertisements for those cars from
autotrader.co.uk.

1.  At present, the script uses the CSV file's expected total rather than
the current total number of hits returned by the website.  This is noted
in search_one_car_type; uncomment the specified line to use the website
total instead.

2.  For testing purposes the main() module currently only tests a few lines
of the CSV file and only outputs one Advertisement object to the console.
Also, logging is currently set to level INFO at the top of the script.



