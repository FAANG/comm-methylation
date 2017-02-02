#
# Copyright (C) 2016 INRA
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

##### adapted from ez package
ezCor <- 
function(
	data, 
	pool1 = NULL,
	tit, 
	test_alpha = .05
){
	
	z=data.frame()
	z_cor = data.frame()
	i = 1
	j = i
	while(i<=length(data)){
		if(j>length(data)){
			i=i+1
			j=i
		}else{
			x = data[,i]
			y = data[,j]
			temp=as.data.frame(cbind(x,y))
			temp=cbind(temp,names(data)[i],names(data)[j])
			z=rbind(z,temp)
			this_cor = round(cor(x,y),2)
			this_cor.test = cor.test(x,y)
			this_col = ifelse(this_cor.test$p.value<test_alpha,'a','b')
			this_size = (this_cor)^2
			cor_text = ifelse(
				this_cor==0
				, '0'
				, ifelse(
					this_cor==1
					, '1'
					, ifelse(
						this_cor==-1
						, '-1'
						, ifelse(
							this_cor>0
							,substr(format(c(this_cor,.123456789),digits=2)[1],2,4)
							,paste('-',substr(format(c(this_cor,.123456789),digits=2)[1],3,5),sep='')
						)
					)
				)
			)
			b=as.data.frame(cor_text)
			b=cbind(b,this_col,this_size,names(data)[j],names(data)[i])
			z_cor=rbind(z_cor,b)
			j=j+1
		}
	}
	names(z)=c('x','y','x_lab','y_lab')
	z=z[z$x_lab!=z$y_lab,]
	names(z_cor)=c('cor','p','rsq','x_lab','y_lab')
	z_cor=z_cor[z_cor$x_lab!=z_cor$y_lab,]
	diag = melt(data,measure.vars=names(data))
	names(diag)[1] = 'x_lab'
	diag$y_lab = diag$x_lab
	
	labels = ddply(
		diag
		, .(x_lab,y_lab)
		, function(x){
			to_return = data.frame(
				x = 0
				, y = 0
				, label = x$x_lab[1]
			)
			return(to_return)
		}
	)
	
	
	points_layer = layer(
		geom = 'hex'
		, params = list(
		  na.rm = TRUE,
		  fill = "black", 
		  alpha=0.9
		)
		, stat = "binhex"
		, position = "identity"
		, data = z
		, mapping = aes_string(
			x = 'x'
			, y = 'y'
		)
	)
	cor_text_layer = layer(
		geom = 'text'
		, stat = "identity"
		, position = "identity"
		, data = z_cor
		, mapping = aes_string(
			label = 'cor'
			, size = 'rsq'
			, colour = 'p'
		)
		, params = list(
		  x = 0.5
		  , y = 0.5
		  , na.rm = TRUE
		  , color = 'black'
		  , alpha = 0.9
		)
	)
	dens_layer = layer(
		geom = 'density'
		, stat = "density"
		, position = "identity"
		, params = list(
			colour = 'transparent'
			, fill = 'snow4'
			, na.rm = TRUE
		)
		, data = diag
		, mapping = aes(
			x = value, ..scaled..
		)
	)
	y_lab = NULL
	x_lab = NULL
	
	lab_tit <- sapply(strsplit(as.character(labels$x_lab), "[.]"), head, n=1)
	names(lab_tit) <- labels$x_lab
	f = facet_grid(y_lab~x_lab, labeller = as_labeller(lab_tit))
	o = theme(
	  panel.border=element_rect(fill = "transparent", colour="black")
			,panel.grid.minor = element_blank()
			,panel.grid.major = element_blank()
			#,axis.ticks = element_blank()
			#,axis.text.y = element_blank()
			#,axis.text.x = element_blank()
			,axis.title.y = element_blank()
			,axis.title.x = element_blank()
			,legend.position='none'
			,strip.background = element_rect(colour="black", fill = 'white')
			,panel.background=element_rect(fill="white")
	)
	x_scale = scale_x_continuous(limits = c( 0 , 1 ) )
	size_scale = scale_size(limits = c(0,1),range=c(10,15))
	
	
	
	p <- ggplot(z_cor)+
	  points_layer+
	  dens_layer+
	  cor_text_layer+
	  f+
	  o+
	  x_scale+
	  size_scale+
	  ggtitle(tit)
	
	# Make a grob object
	Pg <- ggplotGrob(p)
	
	# Facet strip colours
	if (!is.null(pool1)){
	  cols <- ifelse(labels$x_lab %in% pool1, 
	                 "steelblue2", "springgreen2")
	  
	  strips <- grep(pattern="strip-right", Pg$layout$name)
	  strips <- c(strips, grep(pattern="strip-top", Pg$layout$name))
	  refill <- function(strip, colour){
	    strip[["children"]][[1]][["gp"]][["fill"]] <- colour
	    strip
	  }
	  Pg$grobs[strips] <- mapply(refill, 
	                             strip = Pg$grobs[strips], 
	                             colour = cols,
	                             SIMPLIFY = FALSE)
	}

	grid.newpage()
	grid.draw(Pg)
}



