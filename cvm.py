from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import pandas as pd
import re

options = webdriver.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--disable-gpu')

url1 = 'https://www.listadevedores.pgfn.gov.br/'
driver = webdriver.Chrome(options=options)
driver.get(url1)

# SELECT UF

UF = driver.find_element_by_id('ufInput')
# get options
options = [i.get_attribute("value") for i in UF.find_elements_by_tag_name("option")][1:-1]
UF_field = Select(UF)
UF_field.select_by_value('AL') # loop in options list

# select boxes

# get options
id = ['nat_0', 'nat_1', 'nat_2', 'nat_3', 'nat_4', 'nat_5', 'nat_6']
xpaths = ['//*[@id="'+str(i)+'"]' for i in id]

box = driver.find_element_by_xpath(xpaths[1])
box.is_selected()
driver.execute_script("arguments[0].click();", box)

# presso button CONSULTAR
consult = driver.find_element_by_xpath('/html/body/dev-root/dev-consulta/main/dev-filtros/div[3]/div/div/button[1]')
consult.click()

export = driver.find_element_by_xpath('/html/body/dev-root/dev-consulta/main/dev-resultados/div[3]/div/button[1]')
export.click()

# ler os dados

from zipfile import ZipFile

zf = ZipFile('Consulta_Lista_Devedores_2020_04_08.zip')
df_title = pd.read_fwf('Consulta_Lista_Devedores_2020_04_08.csv', sep=';', skiprows=1)
df = pd.read_csv(zf.open('Consulta_Lista_Devedores_2020_04_08.csv'), sep=';', encoding="ISO-8859-1", skiprows=9)
df['UF'] = df_title.iloc[0][0][-3:-1]
df = df.query('Nome.str.contains("LTDA|EIRELI")==False')
df = df[~df["CPF/CNPJ"].str.contains("\*")].reset_index(drop=1)


# verificando na CVM

url2 = 'https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/CPublica/CiaAb/FormBuscaCiaAb.aspx?TipoConsult=c'
driver = webdriver.Chrome(options=options)
driver.get(url2)

doc = df["CPF/CNPJ"][1]
doc = re.sub(r'[^\w]','', doc)

field = driver.find_element_by_id('txtCNPJNome')
field.clear()
field.send_keys(doc)

cont = driver.find_element_by_id('btnContinuar')
cont.click()

page = BeautifulSoup(driver.page_source, 'lxml')
table = page.find('table', id='dlCiasCdCVM')
tabela_companhia = pd.read_html(str(table), header=0)[0]
tabela_companhia = tabela_companhia.query('`SITUAÇÃO REGISTRO`.str.contains("Cancelado")==False')

first_codigo_cvm = tabela_companhia['CÓDIGO CVM'].values[0]

button = driver.find_element_by_link_text(str(first_codigo_cvm))
button.click()

# select Período radio button
radio = driver.find_element_by_id('rdPeriodo')
radio.click()

dt_ini = driver.find_element_by_id('txtDataIni')
dt_ini.clear()
dt_ini.send_keys('12/03/2010')
hora_ini = driver.find_element_by_id('txtHoraIni')
hora_ini.clear()
hora_ini.send_keys('00:03')

dt_fim = driver.find_element_by_id('txtDataFim')
dt_fim.clear()
dt_fim.send_keys('19/01/2020')
hora_fim = driver.find_element_by_id('txtHoraFim')
hora_fim.clear()
hora_fim.send_keys('01:39')

# CATEGORIA
categories_options = driver.find_element_by_id('cboCategoria')
options = [i.get_attribute("text") for i in categories_options.find_elements_by_tag_name("option")]

categ = driver.find_element_by_class_name('chosen-single')
categ.click()
categ = driver.find_element_by_id('cboCategoria_chosen_input')
categ.send_keys(options[9])
categ.send_keys(Keys.RETURN)


# CLICK CONSULTA
consult = driver.find_element_by_id('btnConsulta')
consult.click()



# TABELA
page = BeautifulSoup(driver.page_source, 'lxml')
table = page.find('table', id='grdDocumentos')
result = pd.read_html(str(table), header=0)[0]

visualiza_doc = driver.find_element_by_xpath('//*[@id="VisualizarDocumento"]')
visualiza_doc.click()

#
new_window = driver.window_handles[0] #CHANGE WINDOW
driver.switch_to.window(new_window)

balanco = driver.find_element_by_id('cmbQuadro')
options = [i.get_attribute("text") for i in balanco.find_elements_by_tag_name("option")]
values = [i.get_attribute("value") for i in balanco.find_elements_by_tag_name("option")]

drop = Select(balanco)
drop.select_by_value(values[3])

## You have to switch to the iframe: ##
driver.switch_to.frame(driver.find_element_by_tag_name("iframe"))
page = BeautifulSoup(driver.page_source, 'lxml')
table = page.find('table', id='ctl00_cphPopUp_tbDados')
result = pd.read_html(str(table), header=0)[0]

## Switch back to the "default content" (that is, out of the iframes) ##
driver.switch_to.default_content()