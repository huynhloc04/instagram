## Workflow


         dev.yml        >>>      stage.yml      >>>     prod.yml
            |                        |                      |
        Push code               Pull request             Push to 
    to any branches                 to                   dev/main
    EXCEPT dev/main               dev/main