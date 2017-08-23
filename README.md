# popstats
A tool to combine population stats and query across dimensions

# how to install

Ideally, PopStats should be a web-UI and there would be no need to install anything.
Thats for later. For now, do the following

1. Download the popstats directory. Use the green "Clone or Download"
  green button and "Download ZIP" option.  

2. Unzip into a directory/folder of your choice. Navigate to that directory in your terminal.

3. Install the YAML python library

      % pip install yaml

4. If your system doesnt have pip this will fail. If so, first install pip as per [these instructions](https://pip.pypa.io/en/stable/installing/) and try step 3 again.

3. Run popstats    

      % popstats india.dat
   
# how to use popstats

1. Test the commands below to get a hang of it.

        > dims      
        Dimensions : ['gender', 'age', 'tier', 'hhi'] 
      
            gender : ['male', 'female']
               age : ['child', 'youth', 'adult', 'mature', 'old']
              tier : ['t1', 't2', 't3', 't4', 't5', 't6', 't7', 't8']
               hhi : ['sec_a0', 'sec_a1', 'sec_a', 'sec_b', 'sec_c', 'sec_d', 'sec_e']
       
5. Get the number of male youths in tier-2 cities.
    
        > $male-youth-t2
        t2-male-youth	 :       9,506,700 

6. Plot age vs gender of people living in Tier-1 metros

        > #age-gender$t1 
                      t1	 :      81,000,000 
                      
                                     male	         female	
                   child	     11,462,850	     11,194,200	
                   youth	      7,150,950	      6,687,900	
                   adult	     12,371,400	     12,056,850	
                  mature	      7,103,700	      6,590,700	
                     old	      3,277,800	      3,103,650	

7. Type help to get a list of commands

        > help
      

8. Check out how new dimensions are defined by looking at the included dimension files.
  Write your own custom dimension (say, ketchup-consumption.yml) and add it to the system
  
        > add ketchup-consumption.yml

9. Then analyse it in queries combined other existing dimensions

        > #ketchup-tier$youth
