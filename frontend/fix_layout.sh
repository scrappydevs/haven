#!/bin/bash

# Fix the layout by restructuring the video container

FILE="app/patient-view/page.tsx"

# Replace the problematic absolute positioning with proper flexbox
sed -i.bak2 '
s|{/\* Video Display \*/}|{/\* Video/Animation Container \*/}\
              <div className="flex-1 relative rounded-lg overflow-hidden">\
                {/\* Video Display \*/}|

s|<div className="absolute top-0 left-0 right-0 bottom-20 bg-neutral-950 rounded-lg overflow-hidden">|<div className="absolute inset-0 bg-neutral-950">|g

s|<div className="absolute top-0 left-0 right-0 bottom-20 rounded-lg overflow-hidden">|<div className="absolute inset-0">|g

s|{/\* Bottom AI Voice Agent Card \*/}|</div>\
\
              {/\* Bottom AI Voice Agent Card \*/}|

s|<div className="absolute bottom-0 left-0 right-0 z-10">|<div>|

' "$FILE"

echo "Layout fix applied!"
