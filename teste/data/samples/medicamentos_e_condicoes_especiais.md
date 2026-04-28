# Medicamentos e condicoes especiais antes de procedimentos

Documento de conhecimento geral para demo. Em uso real, nenhuma medicacao deve ser alterada pelo bot.

## Regra central

O bot nunca deve orientar iniciar, suspender, trocar dose ou compensar dose de medicamento. Quando a duvida envolver remedios, a resposta deve pedir confirmacao com a equipe da clinica, medico solicitante ou medico que acompanha o paciente.

## Medicamentos que exigem atencao

Encaminhe para a equipe quando o paciente usar:

- anticoagulantes, como varfarina, rivaroxabana, apixabana, dabigatrana ou heparina;
- antiagregantes, como clopidogrel, ticagrelor ou acido acetilsalicilico quando usado por orientacao medica;
- insulina ou outros medicamentos para diabetes;
- metformina em exames com contraste, especialmente se houver doenca renal;
- medicamentos cardiacos, anti-hipertensivos ou diureticos;
- corticoides, imunossupressores ou medicamentos de alto risco;
- suplementos que aumentem risco de sangramento, se citados no protocolo local.

## Diabetes

Pacientes com diabetes podem precisar de ajuste individual por causa do jejum, preparo intestinal, contraste ou horario do exame. O bot deve orientar que confirmem a conduta para insulina, hipoglicemiantes e alimentacao com a equipe responsavel.

Se o paciente relata hipoglicemia, confusao, desmaio, suor frio intenso, vomitos persistentes ou incapacidade de ingerir liquidos durante preparo, encaminhe para atendimento imediato conforme gravidade.

## Anticoagulantes e antiagregantes

Esses medicamentos podem aumentar risco de sangramento em procedimentos com biopsia, retirada de polipos ou intervencoes. A suspensao tambem pode aumentar risco de trombose, AVC ou eventos cardiacos. Por isso, o bot deve dizer que a decisao e individual e precisa ser feita por profissional de saude.

## Gravidez, amamentacao e alergias

Gravidez, suspeita de gravidez, amamentacao, alergia a medicamentos, alergia a contraste, reacao previa a anestesia ou sedacao devem ser informadas antes do procedimento. O bot deve encaminhar para confirmacao com a clinica.

## Doenca renal e contraste

Em exames com contraste, pacientes com doenca renal, transplante renal, dialise, diabetes, desidratacao ou uso de medicamentos que afetam rim podem precisar de avaliacao especifica. O bot nao deve decidir se o contraste pode ser usado.

## Referencias usadas para calibracao

- ASGE, Understanding Upper Endoscopy: https://www.asge.org/home/for-patients/patient-information/understanding-upper-endoscopy
- Mayo Clinic, Colonoscopy: https://www.mayoclinic.org/tests-procedures/colonoscopy/about/pac-20393569
- ACR Manual on Contrast Media: https://www.acr.org/clinical-resources/clinical-tools-and-reference/contrast-manual
- National Kidney Foundation, Contrast Dye and Your Kidneys: https://www.kidney.org/atoz/content/Contrast-Dye-and-Kidneys
