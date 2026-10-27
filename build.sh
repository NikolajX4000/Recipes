mkdir -p ./out/
pdflatex --shell-escape -interaction=nonstopmode -output-directory ./out/ ./recipes
bibtex ./out/recipes
pdflatex --shell-escape -interaction=nonstopmode -output-directory ./out/ ./recipes
pdflatex --shell-escape -interaction=nonstopmode -output-directory ./out/ ./recipes
makeindex -s ./index-style.ist ./out/recipes
makeindex -s ./index-style.ist ./out/drinks
makeindex -s ./index-style.ist ./out/flavor-profile
makeindex -s ./index-style.ist ./out/glass
makeindex -s ./index-style.ist ./out/ingredient
makeindex -s ./index-style.ist ./out/nemlig
pdflatex --shell-escape -interaction=nonstopmode -output-directory ./out/ ./recipes

# Build the searchable website (website/site/)
python3 ./website/build_site.py
