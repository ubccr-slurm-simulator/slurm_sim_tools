#!/usr/bin/env Rscript

# this script installs the needed packages for R to use for the slurm simulator

# installs packages for R from tutorial things
for(pkg in c("ggplot2","gridExtra","cowplot","lubridate","reticulate","dplyr","stringer","rstudioapi")) {
	install.packages(pkg, contriburl=contrib.url("https://cloud.r-project.org/","source"))
	print(paste("installed package",pkg))
}
install.packages("https://cran.r-project.org/src/contrib/stringr_1.4.0.tar.gz", repos = NULL, type="source")

# installs pacakges for RMD
for(pkg in c("evaluate","highr","markdown","yaml","htmltools","caTools","bitops","knitr","jsonlite","base64enc","rprojroot","rmarkdown")) {
	install.packages(pkg, contriburl=contrib.url("https://cloud.r-project.org/","source"))
	print(paste("installed package",pkg))
}
# had to install data.table package 
install.packages("data.table", contriburl=contrib.url("https://cloud.r-project.org/","source"),dependencies=TRUE) 


