# calculating_change

Split into two branches - previous versions (created earlier in thesis process but just uploaded now) & the 'finished' versions in the main branch. 

'v. 15' performs several functions:
1. Identifies which olive fruit fly traps (i.e., sample points) are within buffers (i.e., within a chosen distance of spraying tracks), and stores the date on which these traps were sprayed
2. Disregards 'spraying events' of those same points that sit within 20 days of a prior spraying event, to prevent autocorrelation
3. Produce a large geodataframe with this data - this is the basis for several subsequent codes

Optional parts:
4. Sorts % change in olive fruit fly numbers into bins and calculates the number of traps falling into each bin
5. Produces a map output of average change by region (i.e., the 8 regions of Samos)

The last two outputs are not really used. 

'v. 14' is based on the same data, but only works for one spraying event, to produce outputs for mini maps produced later. 
