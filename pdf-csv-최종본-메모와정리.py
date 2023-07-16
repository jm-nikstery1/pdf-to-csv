"""
pdf를 csv로 변환하기위한 사용한 파이썬 패키지  
pdfplumber와 tabula

하지만 pdfplumber만 사용한 이유 

pdf에 작성된 내용물의 구조에 한계로 인해 pdfplumber만 사용함

tabula의 특징은 pdf에 테이블(표)를 인식함 
pdfplumber의 특징은 pdf에서 한줄씩은 인식함

그런데 pdf에 있는 대략적인 내용물은 

글자가 몇줄씩 있는 부분과
테이블 처럼 생긴 테이블이 있는 부분이 있음
게다가 한페이지를 넘어서는 테이블도 있음

tabula와 pdfplumber를 서로 사용해서 하려고 했는데 

tabula에서 테이블 처럼 생긴 테이블을 인식의 어려움이 있음

테이블 처럼 생긴 테이블이란 - 테이블은 가로줄, 세로줄이 있어야 테이블(표)인데 
이 pdf에 있는 테이블은 가로줄은 있지만 세로줄이 없다 
테이블의 열 부분의 판단은 그저 칸이 띄어져 있는것으로 있음

즉 사람이 보기에는 그나마 테이블로 인식은 하지만 
컴퓨터가 보기에는 테이블로 인식이 어려운점

그리고 테이블이 길어져서 한페이지를 넘게 생성이 되면 
한페이지를 넘는 테이블을 서로 다른 테이블로 인식하는 상황

일부 매우 적은 내용이 있는 테이블은 테이블로 인식하지도 못함 

이런 이유로 tabula는 제외하고 
한줄씩 인식을 하는 pdfplumber로 개발을 진행함

"""
import pdfplumber
# import tabula # JAVA 8 이상, python 3.7 이상
import pandas as pd
import os
import sys
from collections import deque
import time

start_time = time.time()

"""
특징이 Notes가 끝나고 나서 
나오는 특징이며
한 단어 뒤에 # 이 있는 특징 
"""
sub_title_list= [
    "LDN #" , 
    "SDN #" ,
    "HVP #" ,
    "ICP #" ,
    "LCP #" , 
    "LTC #" ,
    "LVS #" ,
    "SVR #" ,
    "SCP #" ,
    "ST #" ,
    "VP #" ,
    "SVP #" , 
    "VTC #" ,
    "VVS #"
]

#필요 없을수도 있음
# 왜냐하면 특이한 항목이 있을수도 있음
# 구버젼 알고리즘에는 필요

"""
구 버젼 알고리즘으로 적어두었지만 
각 항목의 특징 - pdf 마다 거의 다 있는 항목 
그리고 이 항목이 적혀 있는 줄은 - 이 항목만 적혀있음 - 그래서 한줄씩 판단하는 pdfplumber으로 판단 쉬움 
"""
main_title_list = [
    "General Information" ,
    "Constant Property Information" ,
    "Temperature Dependent Properties" , 
    "Absolute Entropy, Ideal Gas" , 
    "Absolute Entropy, Standard State" , 
    "Acentric Factor" ,
    "Activity coefficient" , 
    "Autoignition Temperature" , 
    "Critical Compressibility Factor" , 
    "Critical Pressure" , 
    "Critical Temperature" , 
    "Critical Volume" , 
    "Dielectric Constant" , 
    "Dipole Moment" , 
    "Flash Point" , 
    "Gibbs Energy of Formation, Ideal Gas" , 
    "Gibbs Energy of Formation, Standard State" , 
    "Heat of Combustion" , 
    "Heat of Formation, Ideal Gas" , 
    "Heat of Formation, Standard State" , 
    "Heat of Fusion" , 
    "Heat of Sublimation" ,
    "Henry's law constant" , 
    "Liquid Molar Volume" , 
    "Lower Flammability Limit Percent" , 
    "Lower Flammability Limit Temperature" , 
    "Melting Point" , 
    "Molecular Weight" , 
    "Normal Boiling Point" , 
    "Parachor" , 
    "Radius of Gyration" , 
    "Refractive Index" , 
    "Solubility Parameter" , 
    "Triple Point Pressure" , 
    "Triple Point Temperature" , 
    "Upper Flammability Limit Percent" , 
    "Upper Flammability Limit Temperature" , 
    "Water solubility" , 
    "van der Waals Area" ,
    "van der Waals Volume"
]

# 필요 없을수도 있음 
# 왜냐하면 특이한 항목이 있을수도 있음
# 구버젼 알고리즘에서는 필요

path_dir = "check_pdf/" 

file_list = os.listdir(path_dir)

csv_path = "to_csv"

"""
pdf 이름마다 폴더를 생성후
그 폴더 안에 출력물 정리   
"""
try:
    os.mkdir("./{}".format(csv_path))
except:
    print("to_csv폴더 있음")

"""
dippr 제거용 함수 
pdf를 한줄씩 하면 페이지 마다 있는 중복된 내용 제거용 
"""
def remove_dippr(check_list, word):
    
    if word not in check_list:
        
        return check_list
    
    else:
        check_list.remove(word)
        remove_dippr(check_list, word)


def get_leading_number(s):
    num_str = ""
    for char in s:
        if char.isdigit():
            num_str += char
        else:
            break
    
    return int(num_str)

def remove_main_col_name(main_csv):
    col_names = "Value Units Note Ref Data Type Acceptance Error Source"
    if col_names not in main_csv:

        return main_csv

    else:

        main_csv.remove(col_names)
        remove_main_col_name(main_csv)
        # 페이지가 넘어가는 테이블이 있는경우 반복 제거 


# note와 ref 추출하기 

########## 중요 - main_csv 는 전체다 들어오는것이 아님 - 안되는 것이 있다 ##########

def create_main_csv(main_csv, check_note_num_list, check_ref_num_list, main_csv_df):
    
    main_title_name = main_csv[0] 
    
    # Value Units Note Ref Data Type Acceptance Error Source" 이거 제거
    # 이유는 csv_index 를 편리하게 관리가능
    
    remove_main_col_name(main_csv) ####### col_name 변경 
    # 주말에 코드 다시 작성해보자 - 중복선언 - 메모도 줄이기 

    for csv_index in range(1,len(main_csv)):
        # index - start num - 1        
        # 대신 main_csv_name 의 위치 주의 
        
        main_csv_values = main_csv[csv_index].split(" ")
        
        for index in range(len(main_csv_values)):

            # main_csv -> main_csv_values 추출 - 전체 반복문이 되야함 

            #######  필수 변수들 초기화  ######
            note_value = set()
            ref_value = set()

            # 이 index 의 기준은 main_csv_values 리스트임
            # 항상 값이 있는건 아님 - 단 Acceptance 은 항상 있음
            Acceptance_index = None 
            note_value_at_index = None
            ref_value_at_index = None
            units_word_index = None
            error_index = None 

            ####### ref_value 와 note_value 추출하기 #######
            main_csv_values_set = set(main_csv_values)
            check_ref_num_list_set = set(check_ref_num_list)

            # and 로는 판단이 안된고 - set 의 교집합을 의미하는거라 & 로 해야함
            ref_value = main_csv_values_set & check_ref_num_list_set

            main_csv_values_set = set(main_csv_values)
            check_note_num_list_set = set(check_note_num_list)

            # and 로는 판단이 안된고 - set 의 교집합을 의미하는거라 & 로 해야함
            note_value = main_csv_values_set & check_note_num_list_set

            ############ 1. Acceptance -> csv 넣기 ###################

            #Acceptance 먼저 판단 하기  
            # 이 index 의 기준은 main_csv_values 리스트임

            for index in range(len(main_csv_values)):
                if len(main_csv_values[index]) == 1:  ########### 이 기준 필요하나?
                    if main_csv_values[index] != "<" and main_csv_values[index] != ">" and not main_csv_values[index].isnumeric():
                        Acceptance_index = index
            #Acceptance_index - 추출 

            main_csv_df.at[csv_index-1, "Acceptance"] = main_csv_values[Acceptance_index]

            #Acceptance_index - csv 에 추가 

            ############ 2.ref 와 note -> csv 넣기 ###################

            if note_value and ref_value:

                # 2개 다 값이 있음 
                # 위치를 알아야함 - ref_value 나 note_value 
                
                ref_value = list(ref_value)[0]
                note_value = list(note_value)[0]
                
                ref_value_at_index = main_csv_values.index(ref_value)
                note_value_at_index = main_csv_values.index(note_value)

                main_csv_df.at[csv_index-1, "Ref"] = ref_value
                main_csv_df.at[csv_index-1, "Note"] = note_value

                ##### Data Type #####
                
                data_type_word = main_csv_values[ref_value_at_index+1 : Acceptance_index]
                
                if len(data_type_word) == 2:
                    data_type_word = data_type_word[0] + " " + data_type_word[1]                    
                    main_csv_df.at[csv_index-1, "Data Type"] = data_type_word
                    
                elif len(data_type_word) == 1:
                    
                    main_csv_df.at[csv_index-1, "Data Type"] = data_type_word[0]


                ##### Units #####

                if note_value_at_index-1 != 2:
                    units_word = main_csv_values[note_value_at_index-1]
                    main_csv_df.at[csv_index-1, "Units"] = units_word
                    units_word_index = main_csv_values.index(units_word)
                    
                elif note_value_at_index-1 == 2:
                    units_word = main_csv_values[note_value_at_index-2] + " " + main_csv_values[note_value_at_index-1]
                    
                    main_csv_df.at[csv_index-1, "Units"] = units_word
                    units_word_index = main_csv_values.index(main_csv_values[note_value_at_index-2])


            elif not note_value and ref_value:

                # note_value 만 값이 없는 경우
                # 위치를 알아야함 - ref_value 
                
                ref_value = list(ref_value)[0]

                ref_value_at_index = main_csv_values.index(ref_value)
                main_csv_df.at[csv_index-1, "Ref"] = ref_value

                ##### Data Type #####
                data_type_word = main_csv_values[ref_value_at_index+1 : Acceptance_index]

                if len(data_type_word) == 2:
                    data_type_word = data_type_word[0] + " " + data_type_word[1]
                    main_csv_df.at[csv_index-1, "Data Type"] = data_type_word
                    
                elif len(data_type_word) == 1:
                    
                    main_csv_df.at[csv_index-1, "Data Type"] = data_type_word[0]

                ##### Units #####

                if ref_value_at_index-1 != 2:
                    units_word = main_csv_values[ref_value_at_index-1]

                    main_csv_df.at[csv_index-1, "Units"] = units_word

                    units_word_index = main_csv_values.index(units_word)
                    
                elif ref_value_at_index-1 == 2:
                    units_word = main_csv_values[ref_value_at_index-2] + " " + main_csv_values[ref_value_at_index-1]
                    
                    main_csv_df.at[csv_index-1, "Units"] = units_word
                    units_word_index = main_csv_values.index(main_csv_values[ref_value_at_index-2])


            elif note_value and not ref_value:

                # ref_value 만 값이 없는 경우
                # 위치를 알아야함 - note_value
                note_value = list(note_value)[0]
                
                note_value_at_index = main_csv_values.index(note_value)
                main_csv_df.at[csv_index-1, "Note"] = note_value

                ##### Data Type #####
                data_type_word = main_csv_values[note_value_at_index+1 : Acceptance_index]

                if len(data_type_word) == 2:
                    data_type_word = data_type_word[0] + " " + data_type_word[1]
                    main_csv_df.at[csv_index-1, "Data Type"] = data_type_word
                    
                elif len(data_type_word) == 1:
                    
                    main_csv_df.at[csv_index-1, "Data Type"] = data_type_word[0]

                ##### Units #####
                if note_value_at_index-1 != 2:
                    units_word = main_csv_values[note_value_at_index-1]

                    main_csv_df.at[csv_index-1, "Units"] = units_word

                    units_word_index = main_csv_values.index(units_word)
                    
                elif note_value_at_index-1 == 2:
                    units_word = main_csv_values[note_value_at_index-2] + " " + main_csv_values[note_value_at_index-1]
                    
                    main_csv_df.at[csv_index-1, "Units"] = units_word
                    units_word_index = main_csv_values.index(main_csv_values[note_value_at_index-2])


            elif not note_value and not ref_value:
                print("Both note_value and ref_value are empty sets")
                
                # 2개다 값이 없음 

                print(main_csv, check_note_num_list, check_ref_num_list)
                
                print("main_csv----------", main_csv)
                
                print("main_title_name========", main_title_name)
                
                raise Exception("살펴보기 아이디어는 항목을 보고 판단")


            ############ 3. Error 값 -> csv 넣기 ###################  
            
            try:

                if str(main_csv_values.index("<")).isnumeric():

                    error_index = main_csv_values.index("<")
                    error_value = main_csv_values[error_index] + " " + main_csv_values[error_index+1]
                    error_index = error_index + 1 
                    main_csv_df.at[csv_index-1, "Error"] = error_value

            except:
                
                try:
                                    
                    if str(main_csv_values.index("Unknown")).isnumeric():

                        error_index = main_csv_values.index("Unknown")
                        error_value = main_csv_values[error_index]
                        main_csv_df.at[csv_index-1, "Error"] = error_value
                    
                except:
                    
                    if note_value_at_index == None and ref_value_at_index == None:
                        """
                        note_value_at_index = None
                        ref_value_at_index = None
                        조건일경우 
                        """
                        print("pass error_index = None 전달 ")
                        pass
                

            ############ 4. Source 값 -> csv 넣기 ###################

            # error_index 는 Source 를 선택하기 위하게 처리됨

            if error_index != None:

                try :
                    if main_csv_values[error_index+1] == main_csv_values[-1]:

                        main_csv_df.at[csv_index-1, "Source"] = main_csv_values[error_index+1]
                except:

                    pass
                    #만약 error_index 가 마지막이면 밑의 조건문이 실행 안됨 - Source 도 없다는 뜻

            elif error_index == None:

                try:
                    if main_csv_values[Acceptance_index+1] == main_csv_values[-1]:

                        main_csv_df.at[csv_index-1, "Source"] = main_csv_values[Acceptance_index+1]

                except:

                    pass
                    #만약 Acceptance_index 가 마지막이면 밑의 조건문이 실행 안됨 - Source 도 없다는 뜻

            ############ 5. Value 값 -> csv 넣기 ###################
            
            # Value 값 항상 있는게 아니다 
            
            if units_word_index == 1:

                main_csv_df.at[csv_index-1, "Value"] = main_csv_values[units_word_index-1]

            elif units_word_index == 0:
                #print("values 의 값이 없다 ")
                pass
                    
            elif units_word_index == None:
                pass



    return  main_csv_df, main_title_name

"""
Temperature Dependent Properties - TDP 생성
"""
def create_tdp_csv(tdp_list):
    
    csv_row_count = 0 # 위에 합칠때 생각해야함

    tdp_title_name = tdp_list[0]
    tdp_col_names = tdp_list[1].split(" ")

    tdp_pro_name_list = []

    if tdp_title_name == "Temperature Dependent Properties":
        print("Temperature Dependent Properties 시작 ")

    else :
        print("TDP - 알고리즘 에러 - 위에 test_page 부분을 확인 ")
        raise ValueError

    tdp_csv_df = pd.DataFrame(columns=tdp_col_names)

    tdp_pro_name = []

    for index in range(len(tdp_list)-1, 1, -1):
        # 2까지임 - 0 과 1은 위에서 사용됨     
        tdp_value_list = tdp_list[index].split(" ")

        if len(tdp_value_list) < 5:

            """
            순서가 바뀐이유 - 이름 항목을 쉽게 합치기 위해서
            """
            for i in range(len(tdp_value_list)-1,-1,-1):

                try:
                    if tdp_value_list[i].isalpha() == True:

                        tdp_pro_name.append(tdp_value_list[i])

                    elif tdp_value_list[i].isalpha() != True:
                        if not tdp_value_list[i]:
                            #print(Empty list)
                            pass

                        else:
                            tdp_csv_df.loc[csv_row_count ,"Quality"] = tdp_value_list[i]

                except:
                    pass


        elif len(tdp_value_list) >= 5:

            csv_col_count = 0

            for i in range(len(tdp_value_list)-1,-1,-1):

                if tdp_value_list[i].isalpha() != True:
                    csv_col_count += 1

                    if tdp_value_list[i] == "<":

                        csv_col_count -= 1
                        continue

                    tdp_csv_df.loc[csv_row_count ,tdp_col_names[-(csv_col_count)]] = tdp_value_list[i]


                elif tdp_value_list[i].isalpha() == True:
                    try:

                        tdp_pro_name.append(tdp_value_list[i])

                    except:
                        #비어있는 단어
                        pass


            tdp_pro_name.reverse()

            tdp_pro_name = " ".join(tdp_pro_name)

            tdp_pro_name_list.append(tdp_pro_name)

            tdp_pro_name = []

        csv_row_count += 1

    return tdp_csv_df, tdp_title_name, tdp_pro_name_list

pdf_list_references =[] # -어디까지 했는지 알려줄수도 있음 - 리스트 초기화 불필요
pdf_list_notes =[] # -어디까지 했는지 알려줄수도 있음 - 리스트 초기화 불필요
pdf_list_RN_error = [] # 만약 References와 Notes의 갯수가 고정한것과 다를때

for i in range(len(file_list)):
    pdf = pdfplumber.open("./pdf/{}".format(file_list[i]))
    pages = pdf.pages[:]
    
    pdf_name = file_list[i].split(".pd")[0]
    
    try:
        os.mkdir("./to_csv/{}".format(pdf_name))
              
        try:
            os.mkdir("./{}/{}/main_title_list".format(csv_path, pdf_name))
            
            os.mkdir("./{}/{}/sub_title_list".format(csv_path, pdf_name))
            
            print("{}시작".format(pdf_name))
        
        except:
            print("{}안의 폴더 있음".format(pdf_name))
        
    except:
        print("{}폴더 있음".format(pdf_name))
    
    
    test_page = [] #항상 초기화 해주기 
    for page in pages:
        page_list = page.extract_text().split("\n")
        page_list.pop()
        test_page.extend(page_list) # append로 하면 리스트 안에 리스트 형식으로 들어가서 2차원리스트 됨


    ########### General_Information ###########
    gi_word = "General Information" # 이거 굳이 필요할까?
    cpi_word = "Constant Property Information"

    gi_index = []
    cpi_index = []

    ###References와 Notes 위치 확인
    references_word = "References"
    notes_word = "Notes"

    references_index = []
    notes_index = []


    ### Temperature Dependent Properties 위치 확인
    t_choice = "Temperature Dependent Properties"
    t_choice_index = []


    ### Absolute Entropy, Ideal Gas 위치 확인 - 이거 필요하나? - 다른 방법으로 가능한가?
    a_choice = "Absolute Entropy, Ideal Gas"
    a_choice_index = []


    for i in range(len(test_page)):
        if gi_word in test_page[i]:
            gi_index.append(i)  #이거 굳이 필요할까?

        if cpi_word in test_page[i]:
            cpi_index.append(i)

        if references_word in test_page[i]:
            if len(test_page[i]) == 10:
                references_index.append(i)
                # 하나의 문자 라인에 references 가 있으면 references 항목만 추출하는게 아니라 다른 라인도 추출하게되어서 
                # 조건을 추가해서 판독해야함 - 문자열 길이로 판단
            
        if notes_word in test_page[i]:
            if len(test_page[i]) == 5:
                notes_index.append(i)
                # 하나의 문자 라인에 notes 가 있으면 notes 항목만 추출하는게 아니라 다른 라인도 추출하게되어서 
                # 조건을 추가해서 판독해야함 - 문자열 길이로 판단
                
        if t_choice in test_page[i]:
            t_choice_index.append(i)

        if a_choice in test_page[i]:
            a_choice_index.append(i)


    gi_0 =test_page[gi_index[0]: cpi_index[0]]

    general_info = pd.DataFrame(gi_0)
    general_info

    general_info.to_csv("./{}/{}/main_title_list/General Information.csv".format(csv_path, pdf_name), header=False, index=False)
    
    ########### General_Information ###########
    
    
    ########### References 와 Notes ###########
             
    ###LDN 위치 확인 - 없는거도 있다 조건문으로 가야할듯 - ldn 위치 2개중 하나는 삭제 예정
    l_choice = sub_title_list
    l_choice_index = []
    a = -1
    while len(l_choice_index) == 0:
        a += 1
        for i in range(len(test_page)):
            if sub_title_list[a] in test_page[i]:
                l_choice_index.append(i)
  
    
    ###LDN 전체 위치 확인 - 없는거도 있다 조건문으로 가야할듯 - ldn 위치 2개중 하나는 삭제 예정
    l_choice = sub_title_list
    l_choice_all_index = []
    
    for i in sub_title_list:
        for a in range(len(test_page)):
            if i in test_page[a]:
                l_choice_all_index.append(a)
                
    
    ###temp_main 위치 확인 위치 - 조건 뽑는거 위에서 a_choice_index와 l_choice_index 이거로 이용
    
    a_test= int(a_choice_index[0])
    
    r_test = int(references_index[-1])
    
    temp_main_page = test_page[a_test:r_test]
    
    temp_main_choice = main_title_list[:]
    temp_main_choice_index = []

    for i in temp_main_choice:
            for a in range(len(temp_main_page[:])):
                if i in temp_main_page[a]:
                    temp_main_choice_index.append(a)
    
    
    print("{}_temp_main_finish".format(pdf_name))
    
    gi_list =test_page[: cpi_index[0]]

    gi_list.remove(test_page[0])

    general_info_df = pd.DataFrame(gi_list)
    
    general_info_df.to_csv("./{}/{}/main_title_list/General Information.csv".format(csv_path, pdf_name), header=False, index=False)

    casn_list = gi_list[1].split()

    casn_index = casn_list.index("CASN:")
    
    casn_num = casn_list[casn_index+1]
    
    casn_df = pd.DataFrame([casn_num], index=["CASN"])
    
    casn_df.to_csv("./{}/{}/CASN.csv".format(csv_path, pdf_name), header=False)
    
    check_casn_num = casn_df[0][0]
    
    dippr_list = test_page[0]

    dippr_series = pd.Series(dippr_list)
    dippr_df = pd.DataFrame(dippr_series)
    
    dippr_df.to_csv("./{}/{}/dirrp.csv".format(csv_path, pdf_name), header=False, index=False)

    ############# refereces - notes ###############

    refereces_notes_index = []

    refereces_notes_index.extend(references_index)
    refereces_notes_index.extend(notes_index)
    refereces_notes_index.extend(t_choice_index)
    refereces_notes_index.extend(a_choice_index)

    refereces_notes_index.sort()

    ############# refereces - notes ###############

    check_ref_list_raw = []
    check_note_list_raw = []
    # raw - 순서 무작위, 문장이 연결 안됨

    check_ref_list = []
    check_note_list = []
    # 순서 정렬, 문장 연결, 숫자 추출됨

    check_rn_ex_raw = []
    # raw - 순서 무작위, 문장이 연결 안됨, 
    # ex - notes 일듯 하지만 - 마지막 문장들의 모음 

    check_rn_ex = []
    # ex - notes 일듯 하지만 - 마지막 문장들의 모음 

    check_ref_index_list = []
    check_note_index_list = []
    # check list 의 숫자, 문장의 시작 부분의 index 모음

    check_ref_num_list = []
    check_note_num_list = []
    # ref 와 note 의 숫자 모음 - CPI 와 TDP 에 필요함 

    for x in range(len(refereces_notes_index)): # 여기 반복문이 끝나고 리스트 합치고 중복 제거, dippr 제거 

        try:
            # list를 그냥 sort하면 안됨 - 그러면 순서 다 깨짐
            if test_page[refereces_notes_index[x]] == "References" :

                check_ref_list_raw.extend(test_page[refereces_notes_index[x] : refereces_notes_index[x+1]])

                check_ref_list_raw.remove("References")

            if test_page[refereces_notes_index[x]] == "Notes":

                check_note_list_raw.extend(test_page[refereces_notes_index[x] : refereces_notes_index[x+1]])

                check_note_list_raw.remove("Notes")

        except:
            # refereces_notes_index 마지막에는 LDN 같은 sub 위치를 선택 
            # 맨밑 notes 부분을 여기서 해결 

            check_rn_ex_raw.extend(test_page[refereces_notes_index[-1] : l_choice_all_index[0]])
            check_rn_ex_raw.remove("Notes")
            
            
    # note 의 리스트들이 분할 된것을 합치는 것 
    check_note_list_raw.extend(check_rn_ex_raw)
    
    # DIPPR 제거 
    remove_dippr(check_ref_list_raw, test_page[0])
    
    # DIPPR 제거 
    remove_dippr(check_note_list_raw, test_page[0])
    
    #DIPPR 제거
    remove_dippr(check_rn_ex_raw, test_page[0])
    

    # 리스트 위에 선언함 
    check_ref_index_list = []
    check_note_index_list = []

    for i in range(len(check_ref_list_raw)):

        if check_ref_list_raw[i].split(" ")[0][0].isnumeric() == True and check_ref_list_raw[i].split(" ")[0][-1] == "." :

            # 이건 문장의 시작은 숫자와 . 점으로 되어있음 - 여기서 숫자를 파악해야하고, 문장의 시작도 파악 할수 있다

            if len(check_ref_list_raw[i].split(" ")) >= 2:
                check_ref_index_list.append(i)


    for i in range(len(check_note_list_raw)):

        if check_note_list_raw[i].split(" ")[0][0].isnumeric() == True and check_note_list_raw[i].split(" ")[0][-1] == "." :

            # 이건 문장의 시작은 숫자와 . 점으로 되어있음 - 여기서 숫자를 파악해야하고, 문장의 시작도 파악 할수 있다

            if len(check_note_list_raw[i].split(" ")) >= 2:
                check_note_index_list.append(i)

    check_ref_list_fix_line = []
    check_note_list_fix_line = []

    for i in range(len(check_ref_index_list)):

        try :
            ref_line = check_ref_list_raw[check_ref_index_list[i]: check_ref_index_list[i+1]]
            ref_line = "".join(ref_line)
            check_ref_list_fix_line.append(ref_line)

        except:
            ref_line = check_ref_list_raw[check_ref_index_list[i]: ]
            ref_line = "".join(ref_line)
            check_ref_list_fix_line.append(ref_line)


    for i in range(len(check_note_index_list)):

        try :
            note_line = check_note_list_raw[check_note_index_list[i]: check_note_index_list[i+1]]
            note_line = "".join(note_line)
            check_note_list_fix_line.append(note_line)

        except:
            note_line = check_note_list_raw[check_note_index_list[i]: ]
            note_line = "".join(note_line)
            check_note_list_fix_line.append(note_line)

    
    # 중복 제거 - 순서는 유지 
    check_ref_list_fix_line = list(dict.fromkeys(check_ref_list_fix_line))
    
    # 중복 제거 - 순서는 유지 
    check_note_list_fix_line = list(dict.fromkeys(check_note_list_fix_line))
    
    check_ref_list = sorted(check_ref_list_fix_line, key=get_leading_number)
    check_note_list = sorted(check_note_list_fix_line, key=get_leading_number)

    check_ref_num_list = []
    check_note_num_list = []
    # ref 와 note 의 숫자 모음 - CPI 와 TDP 에 필요함 - 위에 리스트 있다 

    for i in range(len(check_ref_list)):

        ref_num = check_ref_list[i].split(".")[0]
        check_ref_num_list.append(ref_num)

    
    for i in range(len(check_note_list)):

        note_num = check_note_list[i].split(".")[0]
        check_note_num_list.append(note_num)
        
    
    test_page_index_dict = {}
    for i, item in enumerate(test_page):
        test_page_index_dict[item] = i

    # B 리스트의 각 요소에 대해 해당 요소의 인덱스를 찾아서 새로운 리스트를 만듬
    # 만약 B의 요소가 A에 없다면 None을 추가
    main_title_index_list = []
    for item in main_title_list:
        main_title_index_list.append(test_page_index_dict.get(item))

    ############ sub csv - LDN, SDN, HVP ... 등 ##############

    sub_title_index_list = []

    for a in range(len(test_page)):

        find_sub = test_page[a].split(" ")[0:2]

        try:

            if find_sub[1][0] == "#":

                sub_title_index_list.append(a) # 찾은 sub 위치 list 저장 

        except:
            pass


    for index in range(len(sub_title_index_list)):

        try:

            sub_csv_names_list = test_page[sub_title_index_list[index]].split()
            sub_csv_name = sub_csv_names_list[0] + " " + sub_csv_names_list[1]
            #print(index)

            sub_csv_df_list = test_page[sub_title_index_list[index] : sub_title_index_list[index + 1]]

            ##### 예전의 DIPPR 제거 방식이네 ##############
            if test_page[0] in sub_csv_df_list : 

                sub_csv_df_list.remove(test_page[0])


            sub_csv_df = pd.DataFrame(sub_csv_df_list)

            sub_csv_df.to_csv("./to_csv/{}/sub_title_list/{}.csv".format(pdf_name, sub_csv_name), header=False, index=False)


        except:

            sub_csv_df_list_ex = test_page[sub_title_index_list[index] : -1] 
            # -1이 되는 이유 - test_page의 끝까지 가져오면됨 

            sub_csv_names_list = test_page[sub_title_index_list[index]].split()
            sub_csv_name_ex = sub_csv_names_list[0] + " " + sub_csv_names_list[1]


            ##### 예전의 DIPPR 제거 방식이네 ##############
            if test_page[0] in sub_csv_df_list : 

                sub_csv_df_list.remove(test_page[0])


            sub_csv_df_ex = pd.DataFrame(sub_csv_df_list_ex)

            sub_csv_df_ex.to_csv("./to_csv/{}/sub_title_list/{}.csv".format(pdf_name, sub_csv_name_ex), header=False, index=False )


    ################## main title csv ############# 
    main_csv_list_raw = test_page[notes_index[1] : references_index[1]]
    
    remove_dippr(main_csv_list_raw, test_page[0])

    # 무조건 처음에 찾게 되는 문장을 검색함 
    main_csv_list_raw_start_index = main_csv_list_raw.index("Value Units Note Ref Data Type Acceptance Error Source")

    main_csv_list = main_csv_list_raw[main_csv_list_raw_start_index-1:]

    # dict = {} - 같은 요소가 있어서 dict 으로 진행을 못함 
    main_csv_index_list_raw =[]

    for i in range(len(main_csv_list)):
        if main_csv_list[i] == "Value Units Note Ref Data Type Acceptance Error Source":
            main_csv_index_list_raw.append(i)

    main_csv_index_list = []

    for index in main_csv_index_list_raw:

        # 항목이 있는 경우 제외 
        if main_csv_list[index-1] != "Value Units Note Ref Data Type Acceptance Error Source":

            # 항목의 단어 처리용
            main_str_check = str(main_csv_list[index-1])
            main_str_check_re = main_str_check.replace(",","")  # 단어의 쉼표

            main_str_check_re = main_str_check_re.replace("'","")  # henry's 의 법칙에 있는 (')

            main_str_check_re = main_str_check_re.replace(" ","")

            # 알파벳만 있어야 항목 - 여기서 false는 값이 있다는 뜻 
            if main_str_check_re.isalpha():

                main_csv_index_list.append(index-1)
                
                
    main_title_word_list = []

    for i in main_csv_index_list:

        main_title_word_list.append(main_csv_list[i])
        
        
    if len(main_title_word_list) != 37:
        print("main_title_word_list 의 갯수가 37개가 아니다 - 이건 따로 모아서 확인")
        print(pdf_name)
        
    """
    dataframe 을 생성하는 위치는? - def create_main_csv 시작 하기전 
    """
    main_csv_df = pd.DataFrame(columns= ["Value", "Units", "Note", "Ref", "Data Type", "Acceptance", "Error", "Source"])
    
    main_empty_csv_header = ["Value", "Units", "Note", "Ref", "Data Type", "Acceptance", "Error", "Source"]


    cpi_df_list = []  # 임시 데이터프레임을 저장할 리스트 생성
    cpi_df_list_name =[] # 임시 데이터프레임을 저장할 리스트 생성

    # 항목 보기용 - 근데 이게 CPI 에서도 사용될듯 함 
    for i in range(len(main_csv_index_list)):

        main_csv_df = pd.DataFrame(columns= ["Value", "Units", "Note", "Ref", "Data Type", "Acceptance", "Error", "Source"])


        try:
            main_csv = main_csv_list[main_csv_index_list[i] : main_csv_index_list[i+1]]  
            main_title_name = main_csv[0] # 중복선언이지만 진행하기 

            if len(main_csv) >= 3:
                main_csv_df, main_title_name = create_main_csv(main_csv, check_note_num_list, check_ref_num_list, main_csv_df)
                cpi_df_list_name.append(main_title_name) # cpi test - 여기 if 안에서 해야함

            cpi_df_list.append(main_csv_df) # cpi test

            main_csv_df.to_csv("./{}/{}/main_title_list/{}.csv".format(csv_path, pdf_name, main_title_name), header=True, index=False)

        except:

            main_csv = main_csv_list[main_csv_index_list[i] : ]

            main_title_name = main_csv[0] # 중복선언이지만 진행하기 

            if len(main_csv) >= 3:
                main_csv_df, main_title_name = create_main_csv(main_csv, check_note_num_list, check_ref_num_list, main_csv_df)
                cpi_df_list_name.append(main_title_name) # cpi test - 여기 if 안에서 해야함

            cpi_df_list.append(main_csv_df) #cpi test

            main_csv_df.to_csv("./{}/{}/main_title_list/{}.csv".format(csv_path, pdf_name, main_title_name), header=True, index=False)


    cpi_df_csv = pd.concat(cpi_df_list, ignore_index=True)
    
    cpi_temp_df = cpi_df_csv[cpi_df_csv["Acceptance"] == "A"]
    cpi_temp_df = cpi_temp_df.reset_index(drop=True)
    cpi_temp_df.insert(0, "Property", cpi_df_list_name)
    
    cpi_temp_df.to_csv("./{}/{}/Constant Property Information.csv".format(csv_path, pdf_name), header=True, index=False)
                       
    for i in range(len(test_page)):
        if "Combustion Rxn:" in test_page[i]:
            pass

    # TDP - Temperature Dependent Properties
    tdp_list = test_page[t_choice_index[0]: notes_index[1]]
    
    tdp_title_name = tdp_list[0]
                       
    if tdp_title_name == "Temperature Dependent Properties":
        pass
                       
    tdp_col_names = tdp_list[1].split(" ")
                       
    tdp_csv_df, tdp_title_name, tdp_pro_name_list = create_tdp_csv(tdp_list)
    
    tdp_csv_df = tdp_csv_df.reset_index(drop=True)
    row_list = []

    for row in range(len(tdp_csv_df)):
        
        if tdp_csv_df.loc[row].isnull().sum() >= 7:

            tdp_csv_df_fix_row = tdp_csv_df.loc[row]

            for i in range(len(tdp_csv_df_fix_row)):
                if tdp_csv_df_fix_row[i] == "100%":
                    tdp_csv_df.loc[row+1, "Quality"] = "100%"
                    row_list.append(row)
    
    tdp_csv_df = tdp_csv_df.drop(row_list)
    
    tdp_csv_df = tdp_csv_df.reset_index(drop=True)
    
    for i in range(len(tdp_csv_df)):
        
        if pd.isna(tdp_csv_df.loc[i, 'Quality']):
            pass  # 'Quality'가 NaN인 경우 무시
        
        else:
            tdp_csv_df.loc[i, 'Quality'] = "< " + str(tdp_csv_df.loc[i, 'Quality'])  
                       
    """
    뒤집기 전에 - index 리셋
    Property 이름넣기
    """

    tdp_csv_df = tdp_csv_df.reset_index(drop=True)
                       
                       
    tdp_csv_df["Property"] = tdp_pro_name_list
                       
    """
    거꾸로 생성해서 
    마지막에 데이터프레임을 한번 뒤집어야함 
    """
    tdp_csv_df = tdp_csv_df[::-1]
                       
                       
    tdp_csv_df = tdp_csv_df.reset_index(drop=True)
                       
    tdp_csv_df.to_csv("./{}/{}/Temperature Dependent Properties.csv".format(csv_path, pdf_name), header=True, index=False)

end_time = time.time()


elapsed_time = end_time - start_time
print(f"The code took {elapsed_time} seconds to run")
