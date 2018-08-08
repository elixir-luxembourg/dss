
from tests.base_test import BaseTest
from elixir_dcp.forms import SignupForm


class FormValidatorsTest(BaseTest):

    def test_signup_form(self):
        f1 = SignupForm(elixir_sub_id="DUMMY ELIXIR SUB ID NOT VALIDATED",
                       first_name="Pinar",
                         last_name="á è í ö â ñ ç ř α Š ", phone_no="125736 87--34 ",  institution ="ELU_I_77", email="pinar.alper@uni.lu")


        self.assertTrue(f1.validate())

        f2 = SignupForm(elixir_sub_id="DUMMY ELIXIR SUB ID NOT VALIDATED",
                    first_name="Pinar1 23 ",
                    last_name="è í ö â ñ ç ř α Š", phone_no="125736 87--34 ",  institution ="ELU_I_77", email="pinar.alper@uni.lu")
        self.assertTrue(f2.validate())


        f3 = SignupForm(elixir_sub_id="DUMMY ELIXIR SUB ID NOT VALIDATED",
                        first_name="Pinar",
                        last_name="Alper958945", phone_no="125736 87<tags></tags>34 ",  institution ="ELU_I_77", email="pinar.alper@uni.lu")
        self.assertFalse(f3.validate())
        print(f3.errors)

        f4 = SignupForm(elixir_sub_id="DUMMY ELIXIR SUB ID NOT VALIDATED",
                        first_name="Pinar",
                        last_name="Alper", phone_no="125736 87-DROP TABLE;-34 ",  institution ="ELU_I_77", email="pinar.alper@uni.lu", addr_line1=None, addr_line2=None)
        self.assertFalse(f4.validate())
        print(f4.errors)

        f5 = SignupForm(elixir_sub_id="DUMMY ELIXIR SUB ID NOT VALIDATED",
                        first_name="Pinar<>",
                        last_name="Alper",phone_no="125736 87--34 ",  institution ="ELU_I_77", email="pinar.alper@uni.lu")
        self.assertFalse(f5.validate())
        print(f5.errors)

        f6 = SignupForm(elixir_sub_id="DUMMY ELIXIR SUB ID NOT VALIDATED",
                        first_name="Pinar",
                        last_name="Alper",phone_no="+44 125736 87--34 ",  institution ="ELU_I_77", email="pinar.alper@uni.lu", addr_line1="2 Rue John Lennon", addr_line2="BELVAL-894375" )

        self.assertTrue(f6.validate())



