/********************************************************************************
** Form generated from reading UI file 'gui_pouetG30106.ui'
**
** Created by: Qt User Interface Compiler version 5.5.1
**
** WARNING! All changes made in this file will be lost when recompiling UI file!
********************************************************************************/

#ifndef GUI_POUETG30106_H
#define GUI_POUETG30106_H

#include <QtCore/QVariant>
#include <QtWidgets/QAction>
#include <QtWidgets/QApplication>
#include <QtWidgets/QButtonGroup>
#include <QtWidgets/QCheckBox>
#include <QtWidgets/QDateTimeEdit>
#include <QtWidgets/QDialog>
#include <QtWidgets/QDoubleSpinBox>
#include <QtWidgets/QFrame>
#include <QtWidgets/QHeaderView>
#include <QtWidgets/QLabel>
#include <QtWidgets/QPushButton>
#include <QtWidgets/QSpinBox>
#include <QtWidgets/QTabWidget>
#include <QtWidgets/QTableWidget>
#include <QtWidgets/QToolButton>
#include <QtWidgets/QWidget>

QT_BEGIN_NAMESPACE

class Ui_POUET
{
public:
    QLabel *label_12;
    QLabel *label_13;
    QFrame *frame;
    QLabel *label;
    QDateTimeEdit *config_time;
    QLabel *label_14;
    QFrame *frame_2;
    QDoubleSpinBox *visibility_airmass;
    QLabel *label_15;
    QLabel *label_16;
    QSpinBox *visibility_moon_angle;
    QPushButton *visibility_plot;
    QTabWidget *tabWidget;
    QWidget *obs;
    QTableWidget *tableWidget;
    QWidget *program;
    QLabel *label_27;
    QWidget *night;
    QLabel *label_24;
    QWidget *weather;
    QPushButton *weather_refresh_now;
    QLabel *label_9;
    QLabel *label_5;
    QLabel *label_8;
    QLabel *label_4;
    QLabel *label_2;
    QLabel *label_6;
    QLabel *label_3;
    QLabel *label_7;
    QLabel *label_10;
    QLabel *label_11;
    QWidget *config;
    QCheckBox *config_clouds_analyse;
    QCheckBox *config_wind_analyse;
    QLabel *label_18;
    QToolButton *toolButton;
    QLabel *label_19;
    QLabel *label_20;
    QSpinBox *config_weather_update_every;
    QLabel *label_21;
    QFrame *line_4;
    QCheckBox *config_clouds_auto_update;
    QCheckBox *config_wind_auto_update;
    QFrame *line_5;
    QLabel *label_22;
    QCheckBox *config_show_obs_visibility;
    QCheckBox *config_show_obs_allsky;
    QLabel *label_25;
    QLabel *label_26;
    QWidget *log;
    QLabel *label_28;
    QPushButton *update_obs;
    QPushButton *clouds_refresh_now;

    void setupUi(QDialog *POUET)
    {
        if (POUET->objectName().isEmpty())
            POUET->setObjectName(QStringLiteral("POUET"));
        POUET->resize(1368, 1008);
        label_12 = new QLabel(POUET);
        label_12->setObjectName(QStringLiteral("label_12"));
        label_12->setGeometry(QRect(1150, 10, 201, 21));
        QFont font;
        font.setPointSize(8);
        font.setBold(false);
        font.setWeight(50);
        label_12->setFont(font);
        label_12->setAlignment(Qt::AlignRight|Qt::AlignTrailing|Qt::AlignVCenter);
        label_13 = new QLabel(POUET);
        label_13->setObjectName(QStringLiteral("label_13"));
        label_13->setGeometry(QRect(900, 10, 201, 21));
        QFont font1;
        font1.setBold(true);
        font1.setWeight(75);
        label_13->setFont(font1);
        label_13->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);
        frame = new QFrame(POUET);
        frame->setObjectName(QStringLiteral("frame"));
        frame->setGeometry(QRect(900, 40, 461, 461));
        frame->setFrameShape(QFrame::StyledPanel);
        frame->setFrameShadow(QFrame::Raised);
        label = new QLabel(POUET);
        label->setObjectName(QStringLiteral("label"));
        label->setGeometry(QRect(20, 10, 131, 31));
        label->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);
        config_time = new QDateTimeEdit(POUET);
        config_time->setObjectName(QStringLiteral("config_time"));
        config_time->setGeometry(QRect(150, 10, 161, 27));
        config_time->setAutoFillBackground(false);
        config_time->setCalendarPopup(true);
        label_14 = new QLabel(POUET);
        label_14->setObjectName(QStringLiteral("label_14"));
        label_14->setGeometry(QRect(900, 510, 81, 21));
        label_14->setFont(font1);
        label_14->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);
        frame_2 = new QFrame(POUET);
        frame_2->setObjectName(QStringLiteral("frame_2"));
        frame_2->setGeometry(QRect(900, 540, 461, 461));
        frame_2->setFrameShape(QFrame::StyledPanel);
        frame_2->setFrameShadow(QFrame::Raised);
        visibility_airmass = new QDoubleSpinBox(POUET);
        visibility_airmass->setObjectName(QStringLiteral("visibility_airmass"));
        visibility_airmass->setGeometry(QRect(1040, 510, 51, 27));
        visibility_airmass->setDecimals(1);
        visibility_airmass->setMinimum(0.1);
        visibility_airmass->setMaximum(4);
        visibility_airmass->setSingleStep(0.1);
        visibility_airmass->setValue(1.5);
        label_15 = new QLabel(POUET);
        label_15->setObjectName(QStringLiteral("label_15"));
        label_15->setGeometry(QRect(980, 510, 61, 21));
        QFont font2;
        font2.setBold(false);
        font2.setWeight(50);
        label_15->setFont(font2);
        label_15->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);
        label_16 = new QLabel(POUET);
        label_16->setObjectName(QStringLiteral("label_16"));
        label_16->setGeometry(QRect(1100, 510, 131, 21));
        label_16->setFont(font2);
        label_16->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);
        visibility_moon_angle = new QSpinBox(POUET);
        visibility_moon_angle->setObjectName(QStringLiteral("visibility_moon_angle"));
        visibility_moon_angle->setGeometry(QRect(1230, 510, 48, 27));
        visibility_moon_angle->setMaximum(180);
        visibility_moon_angle->setValue(90);
        visibility_plot = new QPushButton(POUET);
        visibility_plot->setObjectName(QStringLiteral("visibility_plot"));
        visibility_plot->setGeometry(QRect(1290, 510, 71, 27));
        tabWidget = new QTabWidget(POUET);
        tabWidget->setObjectName(QStringLiteral("tabWidget"));
        tabWidget->setGeometry(QRect(10, 50, 871, 951));
        tabWidget->setTabShape(QTabWidget::Rounded);
        obs = new QWidget();
        obs->setObjectName(QStringLiteral("obs"));
        tableWidget = new QTableWidget(obs);
        tableWidget->setObjectName(QStringLiteral("tableWidget"));
        tableWidget->setGeometry(QRect(250, 110, 256, 192));
        tabWidget->addTab(obs, QString());
        program = new QWidget();
        program->setObjectName(QStringLiteral("program"));
        label_27 = new QLabel(program);
        label_27->setObjectName(QStringLiteral("label_27"));
        label_27->setGeometry(QRect(190, 150, 541, 21));
        label_27->setFont(font2);
        label_27->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);
        tabWidget->addTab(program, QString());
        night = new QWidget();
        night->setObjectName(QStringLiteral("night"));
        label_24 = new QLabel(night);
        label_24->setObjectName(QStringLiteral("label_24"));
        label_24->setGeometry(QRect(160, 100, 541, 21));
        label_24->setFont(font2);
        label_24->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);
        tabWidget->addTab(night, QString());
        weather = new QWidget();
        weather->setObjectName(QStringLiteral("weather"));
        weather_refresh_now = new QPushButton(weather);
        weather_refresh_now->setObjectName(QStringLiteral("weather_refresh_now"));
        weather_refresh_now->setGeometry(QRect(20, 170, 111, 27));
        label_9 = new QLabel(weather);
        label_9->setObjectName(QStringLiteral("label_9"));
        label_9->setGeometry(QRect(150, 140, 41, 21));
        label_9->setFont(font2);
        label_9->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);
        label_5 = new QLabel(weather);
        label_5->setObjectName(QStringLiteral("label_5"));
        label_5->setGeometry(QRect(150, 50, 41, 21));
        label_5->setFont(font2);
        label_5->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);
        label_8 = new QLabel(weather);
        label_8->setObjectName(QStringLiteral("label_8"));
        label_8->setGeometry(QRect(150, 110, 41, 21));
        label_8->setFont(font2);
        label_8->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);
        label_4 = new QLabel(weather);
        label_4->setObjectName(QStringLiteral("label_4"));
        label_4->setGeometry(QRect(190, 20, 201, 21));
        label_4->setFont(font);
        label_4->setAlignment(Qt::AlignRight|Qt::AlignTrailing|Qt::AlignVCenter);
        label_2 = new QLabel(weather);
        label_2->setObjectName(QStringLiteral("label_2"));
        label_2->setGeometry(QRect(20, 20, 201, 21));
        label_2->setFont(font1);
        label_2->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);
        label_6 = new QLabel(weather);
        label_6->setObjectName(QStringLiteral("label_6"));
        label_6->setGeometry(QRect(150, 80, 41, 21));
        label_6->setFont(font2);
        label_6->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);
        label_3 = new QLabel(weather);
        label_3->setObjectName(QStringLiteral("label_3"));
        label_3->setGeometry(QRect(20, 50, 131, 21));
        label_3->setFont(font2);
        label_3->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);
        label_7 = new QLabel(weather);
        label_7->setObjectName(QStringLiteral("label_7"));
        label_7->setGeometry(QRect(20, 80, 131, 21));
        label_7->setFont(font2);
        label_7->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);
        label_10 = new QLabel(weather);
        label_10->setObjectName(QStringLiteral("label_10"));
        label_10->setGeometry(QRect(20, 110, 131, 21));
        label_10->setFont(font2);
        label_10->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);
        label_11 = new QLabel(weather);
        label_11->setObjectName(QStringLiteral("label_11"));
        label_11->setGeometry(QRect(20, 140, 131, 21));
        label_11->setFont(font2);
        label_11->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);
        tabWidget->addTab(weather, QString());
        config = new QWidget();
        config->setObjectName(QStringLiteral("config"));
        config_clouds_analyse = new QCheckBox(config);
        config_clouds_analyse->setObjectName(QStringLiteral("config_clouds_analyse"));
        config_clouds_analyse->setGeometry(QRect(10, 120, 131, 22));
        config_clouds_analyse->setChecked(true);
        config_wind_analyse = new QCheckBox(config);
        config_wind_analyse->setObjectName(QStringLiteral("config_wind_analyse"));
        config_wind_analyse->setGeometry(QRect(10, 150, 121, 22));
        config_wind_analyse->setChecked(true);
        label_18 = new QLabel(config);
        label_18->setObjectName(QStringLiteral("label_18"));
        label_18->setGeometry(QRect(10, 10, 201, 21));
        label_18->setFont(font1);
        label_18->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);
        toolButton = new QToolButton(config);
        toolButton->setObjectName(QStringLiteral("toolButton"));
        toolButton->setGeometry(QRect(140, 40, 211, 25));
        label_19 = new QLabel(config);
        label_19->setObjectName(QStringLiteral("label_19"));
        label_19->setGeometry(QRect(10, 90, 201, 21));
        label_19->setFont(font1);
        label_19->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);
        label_20 = new QLabel(config);
        label_20->setObjectName(QStringLiteral("label_20"));
        label_20->setGeometry(QRect(10, 40, 201, 21));
        label_20->setFont(font1);
        label_20->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);
        config_weather_update_every = new QSpinBox(config);
        config_weather_update_every->setObjectName(QStringLiteral("config_weather_update_every"));
        config_weather_update_every->setGeometry(QRect(170, 180, 48, 27));
        config_weather_update_every->setMaximum(30);
        config_weather_update_every->setValue(2);
        label_21 = new QLabel(config);
        label_21->setObjectName(QStringLiteral("label_21"));
        label_21->setGeometry(QRect(10, 180, 161, 21));
        label_21->setFont(font2);
        label_21->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);
        line_4 = new QFrame(config);
        line_4->setObjectName(QStringLiteral("line_4"));
        line_4->setGeometry(QRect(10, 70, 911, 16));
        line_4->setFrameShape(QFrame::HLine);
        line_4->setFrameShadow(QFrame::Sunken);
        config_clouds_auto_update = new QCheckBox(config);
        config_clouds_auto_update->setObjectName(QStringLiteral("config_clouds_auto_update"));
        config_clouds_auto_update->setGeometry(QRect(180, 120, 211, 22));
        config_clouds_auto_update->setChecked(true);
        config_wind_auto_update = new QCheckBox(config);
        config_wind_auto_update->setObjectName(QStringLiteral("config_wind_auto_update"));
        config_wind_auto_update->setGeometry(QRect(180, 150, 211, 22));
        config_wind_auto_update->setChecked(true);
        line_5 = new QFrame(config);
        line_5->setObjectName(QStringLiteral("line_5"));
        line_5->setGeometry(QRect(10, 210, 911, 16));
        line_5->setFrameShape(QFrame::HLine);
        line_5->setFrameShadow(QFrame::Sunken);
        label_22 = new QLabel(config);
        label_22->setObjectName(QStringLiteral("label_22"));
        label_22->setGeometry(QRect(10, 230, 201, 21));
        label_22->setFont(font1);
        label_22->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);
        config_show_obs_visibility = new QCheckBox(config);
        config_show_obs_visibility->setObjectName(QStringLiteral("config_show_obs_visibility"));
        config_show_obs_visibility->setGeometry(QRect(10, 260, 411, 22));
        config_show_obs_visibility->setChecked(true);
        config_show_obs_allsky = new QCheckBox(config);
        config_show_obs_allsky->setObjectName(QStringLiteral("config_show_obs_allsky"));
        config_show_obs_allsky->setGeometry(QRect(10, 290, 411, 22));
        config_show_obs_allsky->setChecked(true);
        label_25 = new QLabel(config);
        label_25->setObjectName(QStringLiteral("label_25"));
        label_25->setGeometry(QRect(10, 890, 391, 21));
        label_25->setFont(font1);
        label_25->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);
        label_26 = new QLabel(config);
        label_26->setObjectName(QStringLiteral("label_26"));
        label_26->setGeometry(QRect(470, 890, 391, 21));
        label_26->setFont(font1);
        label_26->setAlignment(Qt::AlignRight|Qt::AlignTrailing|Qt::AlignVCenter);
        tabWidget->addTab(config, QString());
        log = new QWidget();
        log->setObjectName(QStringLiteral("log"));
        label_28 = new QLabel(log);
        label_28->setObjectName(QStringLiteral("label_28"));
        label_28->setGeometry(QRect(130, 150, 541, 21));
        label_28->setFont(font2);
        label_28->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);
        tabWidget->addTab(log, QString());
        update_obs = new QPushButton(POUET);
        update_obs->setObjectName(QStringLiteral("update_obs"));
        update_obs->setGeometry(QRect(360, 10, 141, 27));
        clouds_refresh_now = new QPushButton(POUET);
        clouds_refresh_now->setObjectName(QStringLiteral("clouds_refresh_now"));
        clouds_refresh_now->setGeometry(QRect(1080, 10, 101, 27));

        retranslateUi(POUET);

        tabWidget->setCurrentIndex(5);


        QMetaObject::connectSlotsByName(POUET);
    } // setupUi

    void retranslateUi(QDialog *POUET)
    {
        POUET->setWindowTitle(QApplication::translate("POUET", "Pouet", 0));
        label_12->setText(QApplication::translate("POUET", "Last update: XX.XX.XXZXX:XX:XX", 0));
        label_13->setText(QApplication::translate("POUET", "Current All Sky image", 0));
        label->setText(QApplication::translate("POUET", "Date & Time (UTC)", 0));
        config_time->setDisplayFormat(QApplication::translate("POUET", "dd.MM.yyyy HH:mm", 0));
        label_14->setText(QApplication::translate("POUET", "Visibility", 0));
        label_15->setText(QApplication::translate("POUET", "Airmass:", 0));
        label_16->setText(QApplication::translate("POUET", "Angle to Moon [\302\260]:", 0));
        visibility_plot->setText(QApplication::translate("POUET", "Draw", 0));
        tabWidget->setTabText(tabWidget->indexOf(obs), QApplication::translate("POUET", "Observations", 0));
        label_27->setText(QApplication::translate("POUET", "Here we can select the programs we want to include", 0));
        tabWidget->setTabText(tabWidget->indexOf(program), QApplication::translate("POUET", "Programs", 0));
        label_24->setText(QApplication::translate("POUET", "When does the night begin? When does it end???", 0));
        tabWidget->setTabText(tabWidget->indexOf(night), QApplication::translate("POUET", "Night", 0));
        weather_refresh_now->setText(QApplication::translate("POUET", "Refresh now", 0));
        label_9->setText(QApplication::translate("POUET", "XX.X", 0));
        label_5->setText(QApplication::translate("POUET", "XX.X", 0));
        label_8->setText(QApplication::translate("POUET", "XX.X", 0));
        label_4->setText(QApplication::translate("POUET", "Last update: XX.XX.XXZXX:XX:XX", 0));
        label_2->setText(QApplication::translate("POUET", "Current weather conditions", 0));
        label_6->setText(QApplication::translate("POUET", "XX.X", 0));
        label_3->setText(QApplication::translate("POUET", "Wind speed [m/s]:", 0));
        label_7->setText(QApplication::translate("POUET", "Wind direction [\302\260]:", 0));
        label_10->setText(QApplication::translate("POUET", "Temperature [\302\260C]:", 0));
        label_11->setText(QApplication::translate("POUET", "Humidity [%]:", 0));
        tabWidget->setTabText(tabWidget->indexOf(weather), QApplication::translate("POUET", "Weather", 0));
        config_clouds_analyse->setText(QApplication::translate("POUET", "Analyse clouds", 0));
        config_wind_analyse->setText(QApplication::translate("POUET", "Analyse wind", 0));
        label_18->setText(QApplication::translate("POUET", "Observation site", 0));
        toolButton->setText(QApplication::translate("POUET", "Load configuration file", 0));
        label_19->setText(QApplication::translate("POUET", "Weather analysis", 0));
        label_20->setText(QApplication::translate("POUET", "La Silla", 0));
        label_21->setText(QApplication::translate("POUET", "Weather update [min]", 0));
        config_clouds_auto_update->setText(QApplication::translate("POUET", "Auto-refresh clouds", 0));
        config_wind_auto_update->setText(QApplication::translate("POUET", "Auto-refresh wind", 0));
        label_22->setText(QApplication::translate("POUET", "Observations", 0));
        config_show_obs_visibility->setText(QApplication::translate("POUET", "Show selected objects in visibility tool", 0));
        config_show_obs_allsky->setText(QApplication::translate("POUET", "Show selected objects in All Sky image", 0));
        label_25->setText(QApplication::translate("POUET", "Written by Thibault Kuntzer and Vivien Bonvin, 2018", 0));
        label_26->setText(QApplication::translate("POUET", "https://github.com/vbonvin/POUET", 0));
        tabWidget->setTabText(tabWidget->indexOf(config), QApplication::translate("POUET", "Configuration", 0));
        label_28->setText(QApplication::translate("POUET", "Shows the log files", 0));
        tabWidget->setTabText(tabWidget->indexOf(log), QApplication::translate("POUET", "View logs", 0));
        update_obs->setText(QApplication::translate("POUET", "Update", 0));
        clouds_refresh_now->setText(QApplication::translate("POUET", "Refresh now", 0));
    } // retranslateUi

};

namespace Ui {
    class POUET: public Ui_POUET {};
} // namespace Ui

QT_END_NAMESPACE

#endif // GUI_POUETG30106_H
