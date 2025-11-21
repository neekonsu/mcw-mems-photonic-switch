import gdsfactory as gf

c = gf.components.coupler_adiabatic(length1=20.0,length2=50,length3=30,wg_sep=1,input_wg_sep=3,output_wg_sep=3, dw=0.1, cross_section="strip").copy()
c.draw_ports()
c.plot()
